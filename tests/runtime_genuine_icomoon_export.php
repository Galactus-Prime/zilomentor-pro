<?php
/**
 * Genuine modern IcoMoon beta archive, containing a self-authored glyph.
 * Disposable WordPress only; the harness stages the pinned original ZIP.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}
use ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons;
use ElementorPro\Modules\AssetsManager\AssetTypes\Icons_Manager;
$fixture = WP_CONTENT_DIR . '/zmp-qa-genuine-icomoon/icomoon-export.zip';
if ( ! is_file( $fixture ) || is_link( $fixture ) || hash_file( 'sha256', $fixture ) !== '39474db6e4549190e9a62774fc05dd3ceff016c1c399088f372ccce67cfb12fa' ) {
	throw new \RuntimeException( 'Pinned modern IcoMoon fixture missing or changed' );
}
$workspace = trailingslashit( sys_get_temp_dir() ) . 'zmp-genuine-icomoon-' . strtolower( wp_generate_password( 12, false, false ) );
$zip = $workspace . '/input.zip';
$extracted = $workspace . '/extracted/';
$manager = ( new \ReflectionClass( Custom_Icons::class ) )->newInstanceWithoutConstructor();
$filesystem = Custom_Icons::get_wp_filesystem();
$uploads = trailingslashit( wp_upload_dir( null, false )['basedir'] ) . 'elementor/custom-icons';
$post_id = 0;
$checks = [];
try {
	wp_mkdir_p( $extracted );
	if ( ! copy( $fixture, $zip ) ) {
		throw new \RuntimeException( 'Could not copy pinned modern archive' );
	}
	$result = ( new \ReflectionMethod( $manager, 'extract_zip' ) )->invoke( $manager, $zip, $extracted );
	$checks['modern_zip_extraction'] = true === $result && ! file_exists( $zip );
	if ( true !== $result ) {
		throw new \RuntimeException( 'Modern ZIP extraction failed' );
	}
	$post_id = wp_insert_post( [ 'post_type' => Icons_Manager::CPT, 'post_status' => 'draft', 'post_title' => 'ZMP Modern IcoMoon QA' ], true );
	if ( is_wp_error( $post_id ) || ! $post_id ) {
		throw new \RuntimeException( 'Could not create disposable post' );
	}
	$manager->current_post_id = $post_id;
	$result = ( new \ReflectionMethod( $manager, 'handle_extracted_icon_set' ) )->invoke( $manager, [ 'directory' => $extracted, 'extracted_to' => $extracted ] );
	$config = is_array( $result ) ? ( $result['config'] ?? [] ) : [];
	$checks['actual_modern_importer_config'] = ! is_wp_error( $result ) && 'icomoon' === strtolower( $config['custom_icon_type'] ?? '' )
		&& 'zmp-untitled-project-' === ( $config['prefix'] ?? '' ) && [ 'zmp-star' ] === ( $config['icons'] ?? [] );
	if ( ! $checks['actual_modern_importer_config'] ) {
		throw new \RuntimeException( 'Modern import failed: ' . ( is_wp_error( $result ) ? $result->get_error_code() : 'configuration mismatch' ) );
	}
	$path = get_post_meta( $post_id, '_elementor_icon_set_path', true );
	if ( ! Custom_Icons::is_safe_icon_set_directory( $path ) || ! str_starts_with( basename( rtrim( $path, '/' ) ), 'untitled-project' ) ) {
		throw new \RuntimeException( 'Unexpected modern icon destination' );
	}
	$path = trailingslashit( $path );
	$css = file_get_contents( $path . 'style.css' );
	$checks['modern_generated_glyph_and_existing_font_fallback'] =
		is_string( $css ) && str_contains( $css, '.zmp-untitled-project-zmp-star:before' )
		&& str_contains( $css, '\f000' ) && str_contains( $css, 'fonts/Untitled.woff' )
		&& ! str_contains( $css, 'Untitled.woff2' )
		&& 'wOFF' === file_get_contents( $path . 'fonts/Untitled.woff', false, null, 0, 4 );
	$checks['modern_unrelated_formats_and_demo_not_published'] =
		! file_exists( $path . 'demo.html' ) && ! file_exists( $path . 'svg' )
		&& ! file_exists( $path . 'untitled-project.icomoon.json' ) && ! file_exists( $path . 'WOFF2_ERROR.txt' )
		&& ! file_exists( $extracted );
	$checks['modern_attachment_records_created'] = count( get_attached_media( '', $post_id ) ) > 0;
	$manager->handle_delete_icon_set( $post_id );
	$checks['modern_scoped_delete'] = ! file_exists( $path ) && is_dir( $uploads ) && ! get_attached_media( '', $post_id );
} finally {
	if ( is_int( $post_id ) && $post_id > 0 ) {
		wp_delete_post( $post_id, true );
	}
	$resolved = realpath( $workspace );
	if ( $resolved && dirname( $resolved ) === realpath( sys_get_temp_dir() )
		&& str_starts_with( basename( $resolved ), 'zmp-genuine-icomoon-' ) ) {
		$filesystem->rmdir( $resolved, true );
	}
}
foreach ( $checks as $name => $passed ) {
	echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( 6 !== count( $checks ) || in_array( false, $checks, true ) ) {
	exit( 4 );
}
