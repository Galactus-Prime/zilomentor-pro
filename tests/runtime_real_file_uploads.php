<?php
/**
 * Validate files authored by independent Office, ODF, PDF, image and codec
 * libraries against the exact Form upload verifier in disposable WordPress.
 *
 * No customer upload, production file, network or actual email is used.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}

$root = WP_CONTENT_DIR . '/zmp-qa-real-formats';
$manifest_path = $root . '/manifest.json';
if ( ! is_file( $manifest_path ) ) {
	fwrite( STDERR, "Real-format test fixture manifest is missing\n" );
	exit( 3 );
}
$manifest = json_decode( file_get_contents( $manifest_path ), true );
if ( ! is_array( $manifest ) || 1 !== ( $manifest['format'] ?? null )
	|| 'self-authored' !== ( $manifest['generated'] ?? null )
	|| ! is_array( $manifest['files'] ?? null ) ) {
	fwrite( STDERR, "Invalid real-format fixture manifest\n" );
	exit( 3 );
}
$required = [
	'word.docx' => true,
	'spreadsheet.xlsx' => true,
	'text.odt' => true,
	'sheet.ods' => true,
	'slides.odp' => true,
	'letter.pdf' => true,
	'image.jpg' => true,
	'image.png' => true,
	'silence.wav' => true,
	'video.mp4' => true,
	'forged.pdf' => false,
	'script.txt' => false,
	'image-zip-polyglot.png' => false,
];
if ( array_keys( $required ) !== array_keys( $manifest['files'] ) ) {
	// Sort before comparing so manifest JSON ordering is irrelevant.
	if ( array_diff_key( $required, $manifest['files'] )
		|| array_diff_key( $manifest['files'], $required ) ) {
		fwrite( STDERR, "Real-format manifest does not contain the expected file set\n" );
		exit( 3 );
	}
}
$checks = [];
$validator = '\ElementorPro\Core\Utils';
foreach ( $required as $name => $should_allow ) {
	$path = $root . '/' . $name;
	$meta = $manifest['files'][ $name ] ?? [];
	$signature = is_file( $path ) && ! is_link( $path )
		? hash_file( 'sha256', $path ) : null;
	$expected_signature = $meta['sha256'] ?? null;
	$valid_fixture = is_string( $signature )
		&& is_string( $expected_signature )
		&& hash_equals( $expected_signature, $signature )
		&& filesize( $path ) === ( $meta['size'] ?? -1 )
		&& $should_allow === ( $meta['accepted'] ?? null );
	$checks[ 'real_fixture_integrity_' . $name ] = $valid_fixture;
	$actual = $valid_fixture && $validator::is_form_upload_content_safe( $path, $name );
	$checks[ 'real_format_' . $name . ( $should_allow ? '_accepted' : '_denied' ) ] =
		$actual === $should_allow;
}
foreach ( $checks as $name => $pass ) {
	echo ( $pass ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) !== 26 || in_array( false, $checks, true ) ) {
	exit( 4 );
}
