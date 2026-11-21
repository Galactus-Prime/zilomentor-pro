<?php
/**
 * Real Fontastic icon-pack integration: parse demo markup in temporary
 * directory but never publish HTML files to same-origin public uploads.
 *
 * Only execute in a fresh, disposable WordPress database / uploads tree.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}

$class = '\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets\Fontastic';
if ( ! class_exists( $class ) ) {
	throw new \RuntimeException( 'Fontastic handler missing' );
}

$wp_uploads = wp_upload_dir( null, false );
$source = rtrim( sys_get_temp_dir(), '/\\' ) . '/zmp-icon-html-'
	. strtolower( wp_generate_password( 12, false, false ) );
$pack_name = 'zmp-qa-html-' . strtolower( wp_generate_password( 12, false, false ) );
$destination_root = trailingslashit( $wp_uploads['basedir'] ) . 'elementor/custom-icons';
$destination = '';
$checks = [];
wp_mkdir_p( trailingslashit( $source ) . 'fonts' );
try {
	$css = '@font-face { font-family: "' . $pack_name . '"; }' . "\n"
		. '[class^="zmp-"] { font-family: "' . $pack_name . '"; }' . "\n"
		. '.zmp-star:before { content: "\\ea01"; }' . "\n";
	file_put_contents( trailingslashit( $source ) . 'styles.css', $css );
	file_put_contents( trailingslashit( $source ) . 'icons-reference.html',
		'<html><body><script>window.__zmp_should_not_be_published=1;</script></body></html>' );
	file_put_contents( trailingslashit( $source ) . 'fonts/preview.html',
		'<html><body><script>window.__zmp_nested_demo=1;</script></body></html>' );
	file_put_contents( trailingslashit( $source ) . 'fonts/dummy.woff', 'synthetic-only-font-data' );

	$handler = new $class( trailingslashit( $source ) );
	$checks['icon_pack_reference_html_present_for_temporary_parsing'] =
		$handler->is_valid() && $handler->is_icon_set();

	$handler->handle_new_icon_set();
	$handler->move_files( 0 );
	$config = $handler->build_config();
	$destination = trailingslashit( $destination_root ) . $config['name'];
	$checks['icon_pack_still_builds_css_and_icon_configuration'] =
		is_string( $config['name'] )
		&& 0 === strpos( $config['name'], 'zmp-qa-html-' )
		&& in_array( 'star', (array) $config['icons'], true )
		&& file_exists( trailingslashit( $destination ) . 'styles.css' )
		&& str_contains( (string) $config['url'], 'styles.css' );
	$checks['icon_pack_root_html_never_published'] =
		! file_exists( trailingslashit( $destination ) . 'icons-reference.html' );
	$checks['icon_pack_nested_html_never_published'] =
		! file_exists( trailingslashit( $destination ) . 'fonts/preview.html' );
	$checks['icon_pack_non_html_font_asset_still_published'] =
		file_exists( trailingslashit( $destination ) . 'fonts/dummy.woff' );
} finally {
	// Delete only this generated disposable QA source and destination.
	$source_parent = realpath( dirname( $source ) );
	if ( false !== $source_parent && dirname( $source ) === $source_parent
		&& is_dir( $source ) && 0 === strpos( basename( $source ), 'zmp-icon-html-' ) ) {
		\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons::get_wp_filesystem()
			->rmdir( $source, true );
	}
	$root = realpath( $destination_root );
	$resolved = $destination && realpath( $destination );
	if ( false !== $root && false !== $resolved
		&& dirname( $resolved ) === $root
		&& 0 === strpos( basename( $resolved ), 'zmp-qa-html-' ) ) {
		\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons::get_wp_filesystem()
			->rmdir( $resolved, true );
	}
}

foreach ( $checks as $name => $passed ) {
	echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) !== 5 || in_array( false, $checks, true ) ) {
	exit( 4 );
}
