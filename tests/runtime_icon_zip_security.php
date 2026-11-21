<?php
/**
 * Custom icon ZIP extraction limits and submitted filename safety.
 * Run ONLY inside disposable WordPress with ZMP_ISOLATED_QA=yes.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}

$klass = '\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons';
if ( ! class_exists( $klass ) || ! class_exists( '\ZipArchive' ) ) {
	fwrite( STDERR, "Icon ZIP runtime dependencies unavailable\n" );
	exit( 3 );
}

$reflect = new \ReflectionClass( $klass );
$icons = $reflect->newInstanceWithoutConstructor();
$extract = $reflect->getMethod( 'extract_zip' );
$upload = $reflect->getMethod( 'upload' );
$base = trailingslashit( sys_get_temp_dir() ) . 'zmp-icon-zip-qa-' . wp_generate_password( 14, false, false );
wp_mkdir_p( $base );

$zip_fixture = static function( string $filename, array $entries ) use ( $base ): string {
	$path = $base . '/' . $filename;
	$zip = new \ZipArchive();
	if ( true !== $zip->open( $path, \ZipArchive::CREATE | \ZipArchive::OVERWRITE ) ) {
		throw new \RuntimeException( 'Could not create synthetic ZIP fixture' );
	}
	foreach ( $entries as $name => $body ) {
		if ( ! $zip->addFromString( $name, $body ) ) {
			throw new \RuntimeException( 'Could not add synthetic ZIP entry' );
		}
	}
	$zip->close();
	return $path;
};

$checks = [];
$prior_files = $_FILES;
try {
	$good = $zip_fixture( 'valid.zip', [
		'icon-set/css/icons.css' => '.icon-test { color: red; }',
		'icon-set/fonts/icons.woff2' => 'synthetic-font-bytes',
		'__MACOSX/._icons.css' => 'ignored',
	] );
	$dest = $base . '/valid-extracted';
	$checks['valid_icon_archive_extracts'] =
		true === $extract->invoke( $icons, $good, $dest )
		&& is_file( $dest . '/icon-set/css/icons.css' )
		&& ! file_exists( $dest . '/__MACOSX/._icons.css' )
		&& ! file_exists( $good );

	foreach ( [
		'parent' => [ '../outside.css' => 'not-allowed' ],
		'absolute' => [ '/tmp/zmp-not-allowed.css' => 'not-allowed' ],
		'backslash' => [ 'icons\\bad.css' => 'not-allowed' ],
		'windows_drive' => [ 'C:/icons/bad.css' => 'not-allowed' ],
		'executable_double_extension' => [ 'icons/icon.php.css' => 'not-allowed' ],
		'compression_bomb' => [ 'icons/huge.css' => str_repeat( 'x', 4 * 1024 * 1024 ) ],
	] as $label => $contents ) {
		$archive = $zip_fixture( $label . '.zip', $contents );
		$result = $extract->invoke( $icons, $archive, $base . '/extract-' . $label );
		$checks[ 'reject_' . $label ] = is_wp_error( $result )
			&& 'invalid_icon_archive' === $result->get_error_code()
			&& ! file_exists( $archive )
			&& ! is_file( $base . '/outside.css' );
	}

	// POSIX ZIP symlink attributes should never become extracted filesystem links.
	$symlink_archive = $zip_fixture( 'symlink.zip', [ 'icons/linked.css' => '../outside.css' ] );
	$symlink_zip = new \ZipArchive();
	if ( true !== $symlink_zip->open( $symlink_archive ) ) {
		throw new \RuntimeException( 'Could not reopen ZIP symlink fixture' );
	}
	$symlink_zip->setExternalAttributesName( 'icons/linked.css', 3, 0120777 << 16 );
	$symlink_zip->close();
	$symlink_result = $extract->invoke( $icons, $symlink_archive, $base . '/extract-symlink' );
	$checks['reject_symlink_archive_entry'] =
		is_wp_error( $symlink_result ) && ! file_exists( $symlink_archive );

	$too_many = [];
	for ( $i = 0; $i < 4097; $i++ ) {
		$too_many[ 'icons/' . $i . '.txt' ] = 'x';
	}
	$archive = $zip_fixture( 'too-many.zip', $too_many );
	$result = $extract->invoke( $icons, $archive, $base . '/extract-too-many' );
	$checks['reject_excessive_entry_count'] = is_wp_error( $result )
		&& ! file_exists( $archive );

	// Imports contain arbitrary post-meta strings. They must not turn a
	// custom-icon deletion into a recursive delete of an unrelated directory.
	$icon_root = $base . '/owner-custom-icon-root';
	$allowed = $icon_root . '/one-icon-set';
	$nested = $allowed . '/nested';
	$unrelated = $base . '/unrelated-content';
	wp_mkdir_p( $nested );
	wp_mkdir_p( $unrelated );
	$icon_dir_filter = static function( $value ) use ( $icon_root ) {
		return $icon_root;
	};
	add_filter( 'elementor_pro/icons_manager/custom_icons/dir', $icon_dir_filter );
	try {
		$checks['delete_guard_allows_icon_set_child'] = $klass::is_safe_icon_set_directory( $allowed );
		$checks['delete_guard_rejects_icon_storage_root'] = ! $klass::is_safe_icon_set_directory( $icon_root );
		$checks['delete_guard_rejects_unrelated_directory'] = ! $klass::is_safe_icon_set_directory( $unrelated );
		$checks['delete_guard_rejects_nested_folder'] = ! $klass::is_safe_icon_set_directory( $nested );
		$checks['delete_guard_rejects_missing_or_invalid_paths'] =
			! $klass::is_safe_icon_set_directory( $base . '/missing' )
			&& ! $klass::is_safe_icon_set_directory( [] );
		$symlink = $base . '/icon-directory-symlink';
		$link_created = function_exists( 'symlink' ) && @symlink( $allowed, $symlink );
		$checks['delete_guard_rejects_symlink'] =
			! $link_created || ! $klass::is_safe_icon_set_directory( $symlink );
	} finally {
		remove_filter( 'elementor_pro/icons_manager/custom_icons/dir', $icon_dir_filter );
	}

	$sentinel = $base . '/client-controlled-filename.cfg';
	file_put_contents( $sentinel, 'keep this isolated file' );
	$_FILES['zip_upload'] = [
		'name' => $sentinel,
		'tmp_name' => $sentinel,
		'error' => UPLOAD_ERR_OK,
		'size' => filesize( $sentinel ),
	];
	$result = $upload->invoke( $icons );
	$checks['invalid_extension_does_not_delete_client_filename'] =
		is_wp_error( $result ) && file_exists( $sentinel )
		&& 'keep this isolated file' === file_get_contents( $sentinel );

	// A real PHP multiple-file shape uses nested arrays only in name/tmp_name.
	// Sanitize string filenames without changing the matching upload indices.
	$_FILES['zip_upload'] = [
		'name' => [ 'first' => 'invoice sample.pdf', 'second' => 'photo image.png' ],
		'tmp_name' => [ 'first' => '/tmp/fake-1', 'second' => '/tmp/fake-2' ],
		'error' => [ 'first' => UPLOAD_ERR_OK, 'second' => UPLOAD_ERR_OK ],
	];
	$clean_multi = \ElementorPro\Core\Utils::_unstable_get_super_global_value( $_FILES, 'zip_upload' );
	$checks['sanitize_multi_upload_preserves_file_indices'] =
		is_array( $clean_multi )
		&& 'invoice-sample.pdf' === ( $clean_multi['name']['first'] ?? null )
		&& 'photo-image.png' === ( $clean_multi['name']['second'] ?? null )
		&& '/tmp/fake-2' === ( $clean_multi['tmp_name']['second'] ?? null );

	// Non-string nested names may originate in malicious form-data shapes:
	// they must never reach sanitize_file_name() as an array or number.
	$_FILES['zip_upload'] = [
		'name' => [ 'one' => [ 'nested file.pdf', false ], 'two' => 123 ],
		'tmp_name' => [ 'one' => [ '/tmp/fake-3', '/tmp/fake-4' ], 'two' => '/tmp/fake-5' ],
		'error' => UPLOAD_ERR_OK,
	];
	$malformed = \ElementorPro\Core\Utils::_unstable_get_super_global_value( $_FILES, 'zip_upload' );
	$checks['malformed_upload_names_cannot_trigger_type_error'] =
		is_array( $malformed )
		&& 'nested-file.pdf' === ( $malformed['name']['one'][0] ?? null )
		&& '' === ( $malformed['name']['one'][1] ?? null )
		&& '' === ( $malformed['name']['two'] ?? null );

	$_FILES['zip_upload'] = [
		'name' => [ 'fake.zip' ],
		'tmp_name' => [ '/tmp/none' ],
		'error' => [ UPLOAD_ERR_OK ],
	];
	$checks['reject_malformed_array_upload'] = is_wp_error( $upload->invoke( $icons ) );
} finally {
	$_FILES = $prior_files;
	// Only delete our own disposable temporary test directory.
	if ( is_dir( $base ) ) {
		$walk = new \RecursiveIteratorIterator(
			new \RecursiveDirectoryIterator( $base, \FilesystemIterator::SKIP_DOTS ),
			\RecursiveIteratorIterator::CHILD_FIRST
		);
		foreach ( $walk as $item ) {
			if ( $item->isDir() && ! $item->isLink() ) {
				@rmdir( $item->getPathname() );
			} else {
				@unlink( $item->getPathname() );
			}
		}
		@rmdir( $base );
	}
}

foreach ( $checks as $name => $passed ) {
	echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) < 9 || in_array( false, $checks, true ) ) {
	exit( 4 );
}
