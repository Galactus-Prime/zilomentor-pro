<?php
/**
 * Opt-in genuine Fontello ZIP import and deletion test.
 * The harness stages only the pinned, privately retained generator export.
 * No production WordPress instance or customer assets may be used.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}
use ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons;
use ElementorPro\Modules\AssetsManager\AssetTypes\Icons_Manager;

$fixture = WP_CONTENT_DIR . '/zmp-qa-genuine-fontello/fontello-export.zip';
$expected_hash = '436d8abd74629563cc7efe92d1dcdb1703ebd3c7d3effacfd6a51d0f8a60dbdf';
if ( ! is_file( $fixture ) || is_link( $fixture ) || hash_file( 'sha256', $fixture ) !== $expected_hash ) {
	throw new \RuntimeException( 'Pinned genuine Fontello fixture missing or changed' );
}
$workspace = trailingslashit( sys_get_temp_dir() ) . 'zmp-genuine-fontello-' . strtolower( wp_generate_password( 12, false, false ) );
$zip = $workspace . '/input.zip';
$extracted = $workspace . '/extracted/';
$uploads = trailingslashit( wp_upload_dir( null, false )['basedir'] ) . 'elementor/custom-icons';
$checks = [];
$post_id = 0;
$manager = ( new \ReflectionClass( Custom_Icons::class ) )->newInstanceWithoutConstructor();
$filesystem = Custom_Icons::get_wp_filesystem();
try {
	wp_mkdir_p( $extracted );
	if ( ! copy( $fixture, $zip ) ) {
		throw new \RuntimeException( 'Could not copy pinned archive' );
	}
	$extract = new \ReflectionMethod( $manager, 'extract_zip' );
	$result = $extract->invoke( $manager, $zip, $extracted );
	$checks['genuine_archive_passes_real_zip_extraction'] = true === $result && ! file_exists( $zip );
	if ( true !== $result ) {
		throw new \RuntimeException( 'Real ZIP extraction rejected fixture' );
	}
	$folders = glob( $extracted . '*', GLOB_ONLYDIR );
	if ( count( $folders ) !== 1 ) {
		throw new \RuntimeException( 'Unexpected extracted folder structure' );
	}
	$post_id = wp_insert_post( [
		'post_type' => Icons_Manager::CPT,
		'post_status' => 'draft',
		'post_title' => 'ZMP genuine Fontello isolated QA',
	], true );
	if ( is_wp_error( $post_id ) || ! $post_id ) {
		throw new \RuntimeException( 'Could not create disposable icon post' );
	}
	$manager->current_post_id = $post_id;
	$import = new \ReflectionMethod( $manager, 'handle_extracted_icon_set' );
	$result = $import->invoke( $manager, [
		'directory' => trailingslashit( $folders[0] ),
		'extracted_to' => $extracted,
	] );
	$config = is_array( $result ) ? ( $result['config'] ?? [] ) : [];
	$checks['actual_import_manager_accepts_genuine_pack'] =
		! is_wp_error( $result ) && 'fontello' === strtolower( $config['custom_icon_type'] ?? '' )
		&& 'zmp-qa-' === ( $config['prefix'] ?? '' ) && [ 'edit' ] === ( $config['icons'] ?? [] );
	if ( ! $checks['actual_import_manager_accepts_genuine_pack'] ) {
		throw new \RuntimeException( 'Actual importer rejected genuine export: ' . ( is_wp_error( $result ) ? $result->get_error_code() : 'invalid config' ) );
	}
	$path = get_post_meta( $post_id, '_elementor_icon_set_path', true );
	if ( ! Custom_Icons::is_safe_icon_set_directory( $path ) || ! str_starts_with( basename( rtrim( $path, '/' ) ), 'zmp-qa-public' ) ) {
		throw new \RuntimeException( 'Unexpected icon destination' );
	}
	$path = trailingslashit( $path );
	$css = $path . 'css/zmp-qa-public.css';
	$woff = $path . 'font/zmp-qa-public.woff2';
	$svg = $path . 'font/zmp-qa-public.svg';
	$checks['modern_css_and_real_woff2_published'] =
		is_file( $css ) && is_file( $woff ) && 'wOF2' === file_get_contents( $woff, false, null, 0, 4 )
		&& str_contains( file_get_contents( $css ), '.zmp-qa-edit:before' );
	$checks['legacy_svg_published_without_external_doctype'] =
		is_file( $svg ) && false === stripos( file_get_contents( $svg ), '<!DOCTYPE' );
	$checks['license_preserved_and_optional_active_assets_omitted'] =
		is_file( $path . 'LICENSE.txt' ) && ! file_exists( $path . 'demo.html' )
		&& ! file_exists( $path . 'css/zmp-qa-public-embedded.css' )
		&& ! file_exists( $path . 'css/zmp-qa-public-ie7.css' )
		&& ! file_exists( $path . 'css/zmp-qa-public-ie7-codes.css' );
	$checks['real_import_creates_attachment_records'] =
		count( get_attached_media( '', $post_id ) ) > 0;
	$manager->handle_delete_icon_set( $post_id );
	$checks['actual_delete_removes_pack_and_attachments_not_shared_root'] =
		! file_exists( $path ) && is_dir( $uploads ) && ! get_attached_media( '', $post_id );
} finally {
	if ( is_int( $post_id ) && $post_id > 0 ) {
		wp_delete_post( $post_id, true );
	}
	$resolved = realpath( $workspace );
	if ( $resolved && dirname( $resolved ) === realpath( sys_get_temp_dir() )
		&& str_starts_with( basename( $resolved ), 'zmp-genuine-fontello-' ) ) {
		$filesystem->rmdir( $resolved, true );
	}
}
foreach ( $checks as $name => $passed ) {
	echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( 7 !== count( $checks ) || in_array( false, $checks, true ) ) {
	exit( 4 );
}
