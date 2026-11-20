<?php
/**
 * Synthetic Form Upload security: no network or production files are touched.
 * Runs only inside the disposable WordPress/Fiore Docker database.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
    exit( 2 );
}

$util = '\\ElementorPro\\Core\\Utils';
$legacy = '\\ElementorPro\\Modules\\Forms\\Fields\\Upload';
$atomic = '\\ElementorPro\\Modules\\AtomicForm\\File_Upload\\File_Storage';
$form_file = '\\ElementorPro\\Modules\\AtomicForm\\File_Upload\\Form_File';

if ( ! class_exists( $util ) || ! class_exists( $legacy )
    || ! class_exists( $atomic ) || ! class_exists( $form_file ) ) {
    fwrite( STDERR, "Form upload implementation not registered\n" );
    exit( 3 );
}

$root = sys_get_temp_dir() . '/zmp-uploads-' . wp_generate_password( 12, false );
if ( ! wp_mkdir_p( $root ) ) {
    exit( 3 );
}
$fixture = static function ( $name, $content ) use ( $root ) {
    $path = $root . '/' . $name;
    file_put_contents( $path, $content );
    return $path;
};
$checks = [];
$valid = static function ( $name, $path, $should_pass ) use ( $util, &$checks ) {
    $actual = $util::is_form_upload_content_safe( $path, $name );
    $checks[ $name . ( $should_pass ? '_valid' : '_rejected' ) ] = $actual === $should_pass;
};
try {
    $genuine_pdf = $fixture( 'real.pdf', "%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n" );
    $disguised_pdf = $fixture( 'fake.pdf', "<?php echo 'executed';" );
    $disguised_office = $fixture( 'forged.docx', "<?php echo 'executed';" );
    $script_txt = $fixture( 'script.txt', '<?php echo "executed";');
    $real_txt = $fixture( 'readme.txt', "Hello from disposable ZiloMentor upload QA\n" );
    $script_php8 = $fixture( 'payload.php8', '<?php echo 1;');

    $valid( 'real.pdf', $genuine_pdf, true );
    $valid( 'fake.pdf', $disguised_pdf, false );
    $valid( 'forged.docx', $disguised_office, false );
    $valid( 'script.txt', $script_txt, false );
    $valid( 'readme.txt', $real_txt, true );
    $valid( 'payload.php8', $script_php8, false );

    // Representative media/text fixtures made locally with legitimate file
    // signatures. No production uploads or third-party file downloads.
    $csv = $fixture( 'inventory.csv', "SKU,Price\nDEMO-1,12.50\n" );
    $valid( 'inventory.csv', $csv, true );
    $rtf = $fixture( 'note.rtf', "{\\rtf1\\ansi Synthetic ZiloMentor document}\n" );
    $valid( 'note.rtf', $rtf, true );
    $wave = $fixture( 'silence.wav',
        'RIFF' . pack( 'V', 36 ) . 'WAVEfmt ' .
        pack( 'VvvVVvv', 16, 1, 1, 8000, 8000, 1, 8 ) .
        'data' . pack( 'V', 0 )
    );
    $valid( 'silence.wav', $wave, true );
    $valid( 'forged.wav', $disguised_pdf, false );

    if ( class_exists( '\ZipArchive' ) ) {
        $office_file = $root . '/word.docx';
        $zip = new \ZipArchive();
        $checks['synthetic_office_zip_created'] = true === $zip->open( $office_file, \ZipArchive::CREATE );
        if ( $checks['synthetic_office_zip_created'] ) {
            $zip->addFromString( '[Content_Types].xml', '<Types/>' );
            $zip->addFromString( 'word/document.xml', '<w:document/>' );
            $zip->close();
            $valid( 'word.docx', $office_file, true );

            // Minimal OOXML part/package structure, including
            // presentation/spreadsheet relationships (not empty ZIPs).
            foreach ( [
                'spreadsheet.xlsx' => [ 'xl/workbook.xml',
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets/></workbook>' ],
                'presentation.pptx' => [ 'ppt/presentation.xml',
                    '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>' ],
            ] as $office_name => $office_part ) {
                $ooxml = $root . '/' . $office_name;
                $archive = new \ZipArchive();
                $created = true === $archive->open( $ooxml, \ZipArchive::CREATE );
                $checks[ $office_name . '_fixture_created' ] = $created;
                if ( $created ) {
                    $archive->addFromString( '[Content_Types].xml',
                        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>' );
                    $archive->addFromString( $office_part[0], $office_part[1] );
                    $archive->close();
                    $valid( $office_name, $ooxml, true );
                }
            }

            // ODF uses a mimetype entry and manifest, not OOXML content types.
            foreach ( [
                'text.odt' => 'application/vnd.oasis.opendocument.text',
                'sheet.ods' => 'application/vnd.oasis.opendocument.spreadsheet',
                'slides.odp' => 'application/vnd.oasis.opendocument.presentation',
            ] as $odf_name => $odf_type ) {
                $odf = $root . '/' . $odf_name;
                $archive = new \ZipArchive();
                $created = true === $archive->open( $odf, \ZipArchive::CREATE );
                $checks[ $odf_name . '_fixture_created' ] = $created;
                if ( $created ) {
                    $archive->addFromString( 'mimetype', $odf_type );
                    $archive->setCompressionName( 'mimetype', \ZipArchive::CM_STORE );
                    $archive->addFromString( 'META-INF/manifest.xml',
                        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>' );
                    $archive->addFromString( 'content.xml',
                        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"/>' );
                    $archive->close();
                    $valid( $odf_name, $odf, true );
                }
            }
            $prefixed_office = $root . '/prefixed.docx';
            file_put_contents( $prefixed_office, "fake header" . file_get_contents( $office_file ) );
            $valid( 'prefixed.docx', $prefixed_office, false );
        }
        $not_office = $root . '/fake-zip.docx';
        $zip2 = new \ZipArchive();
        if ( true === $zip2->open( $not_office, \ZipArchive::CREATE ) ) {
            $zip2->addFromString( 'index.txt', 'arbitrary archive' );
            $zip2->close();
            $valid( 'fake-zip.docx', $not_office, false );
        } else {
            $checks['fake_zip_fixture_created'] = false;
        }
    }

    if ( function_exists( 'imagecreatetruecolor' ) ) {
        $image_path = $root . '/tiny.png';
        $image = imagecreatetruecolor( 3, 3 );
        imagepng( $image, $image_path );
        imagedestroy( $image );
        $valid( 'tiny.png', $image_path, true );
        $valid( 'fake.png', $disguised_pdf, false );
        $image_bytes = file_get_contents( $image_path );
        $phar_image = $root . '/phar.png';
        file_put_contents( $phar_image, $image_bytes . "\n__HALT_COMPILER();\n" );
        $valid( 'phar.png', $phar_image, false );
        if ( class_exists( '\\ZipArchive' ) ) {
            $zip_tail = $root . '/archive-tail.zip';
            $archive = new \ZipArchive();
            if ( true === $archive->open( $zip_tail, \ZipArchive::CREATE ) ) {
                $archive->addFromString( 'script.php', '<?php echo "untrusted";' );
                $archive->close();
                $polyglot_image = $root . '/png-zip.png';
                file_put_contents( $polyglot_image, $image_bytes . file_get_contents( $zip_tail ) );
                $valid( 'png-zip.png', $polyglot_image, false );
            } else {
                $checks['png_zip_polyglot_fixture_created'] = false;
            }
        }
    }

    $legacy_form = new $legacy();
    $method = new \ReflectionMethod( $legacy, 'is_uploaded_content_allowed' );
    $checks['legacy_rejects_disguised_pdf'] = false === $method->invoke(
        $legacy_form, $disguised_pdf, 'fake.pdf', [ 'file_types' => 'pdf' ]
    );
    $checks['legacy_accepts_genuine_pdf'] = true === $method->invoke(
        $legacy_form, $genuine_pdf, 'real.pdf', [ 'file_types' => 'pdf' ]
    );
    $checks['legacy_rejects_disguised_office'] = false === $method->invoke(
        $legacy_form, $disguised_office, 'forged.docx', [ 'file_types' => 'docx' ]
    );

    // Regression for CVE-2026-32475-style skipped-first-file handling.
    // An optional empty first item must NEVER let a later executable upload
    // bypass validation. These are in-memory $_FILES fixtures, not HTTP uploads.
    $original_files = $_FILES;
    try {
        $_FILES['form_fields'] = [
            'name' => [ 'synthetic_upload' => [ '', 'second.php' ] ],
            'type' => [ 'synthetic_upload' => [ '', 'application/x-php' ] ],
            'tmp_name' => [ 'synthetic_upload' => [ '', $disguised_pdf ] ],
            'error' => [ 'synthetic_upload' => [ UPLOAD_ERR_NO_FILE, UPLOAD_ERR_OK ] ],
            'size' => [ 'synthetic_upload' => [ 0, filesize( $disguised_pdf ) ] ],
        ];
        $fake_record = ( new \ReflectionClass(
            '\\ElementorPro\\Modules\\Forms\\Classes\\Form_Record'
        ) )->newInstanceWithoutConstructor();
        $ajax_class = '\\ElementorPro\\Modules\\Forms\\Classes\\Ajax_Handler';
        $ajax = new $ajax_class();
        $legacy_form->fixed_files_indices = false;
        $legacy_form->validation( [
            'id' => 'synthetic_upload',
            'required' => false,
            'file_types' => 'pdf',
            'max_files' => 2,
            'file_sizes' => 2,
        ], $fake_record, $ajax );
        $checks['legacy_empty_first_file_does_not_skip_second_php'] =
            ! empty( $ajax->errors['synthetic_upload'] );
        $checks['legacy_empty_first_file_does_not_mark_success'] =
            false === $ajax->is_success;
    } finally {
        $_FILES = $original_files;
    }

    $storage = new $atomic();
    $incoming = new $form_file( 'fake.pdf', 'application/pdf', $disguised_pdf,
        UPLOAD_ERR_OK, filesize( $disguised_pdf ) );
    $result = $storage->store( $incoming );
    $checks['atomic_rejects_spoofed_pdf_before_move'] = isset( $result['error'] );
    $local_file = new $form_file( 'readme.txt', 'text/plain', $real_txt,
        UPLOAD_ERR_OK, filesize( $real_txt ) );
    $local_file_result = $storage->store( $local_file );
    $checks['atomic_refuses_non_http_uploaded_local_file'] =
        isset( $local_file_result['error'] ) && file_exists( $real_txt );

    // Cleanup must not unlink a file outside the dedicated Elementor Form
    // upload directory even if caller input supplies an arbitrary real path.
    $external = $root . '/outside.txt';
    file_put_contents( $external, 'must remain' );
    $storage->delete( [ $external ] );
    $checks['atomic_cleanup_refuses_external_paths'] = file_exists( $external );

    $uploads = wp_upload_dir( null, false );
    $form_dir = trailingslashit( $uploads['basedir'] ) . 'elementor/forms';
    wp_mkdir_p( $form_dir );
    $owned = trailingslashit( $form_dir ) . 'zmp-disposable-' .
        wp_generate_password( 12, false ) . '.txt';
    file_put_contents( $owned, 'synthetic temporary upload' );
    $storage->delete( [ $owned ] );
    $checks['atomic_cleanup_deletes_only_own_file'] = ! file_exists( $owned );
    // Separate benign fixture intentionally remains until the *entire
    // disposable WordPress tree* is destroyed. Nginx header QA fetches it.
    $headers_fixture = trailingslashit( $form_dir ) . 'zmp-qa-header-fixture.txt';
    file_put_contents( $headers_fixture, 'Synthetic ZiloMentor download only.' );
    $checks['synthetic_attachment_header_fixture_created'] =
        is_file( $headers_fixture );
    if ( file_exists( $owned ) ) {
        unlink( $owned );
    }
} finally {
    foreach ( glob( $root . '/*' ) ?: [] as $p ) {
        if ( is_file( $p ) ) {
            unlink( $p );
        }
    }
    rmdir( $root );
}

foreach ( $checks as $name => $pass ) {
    echo ( $pass ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( ! $checks || in_array( false, $checks, true ) ) {
    exit( 4 );
}
