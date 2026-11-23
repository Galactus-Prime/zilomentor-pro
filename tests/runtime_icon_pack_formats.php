<?php
/**
 * Two self-authored, structurally representative custom icon pack exports.
 * Tests built-in Fontello/IcoMoon import handlers with CSS local font refs.
 * Never runs against production WordPress uploads or database.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}
$root = trailingslashit( sys_get_temp_dir() ) . 'zmp-icon-formats-'
	. strtolower( wp_generate_password( 10, false, false ) );
$slug = 'zmp-fmt-' . strtolower( wp_generate_password( 10, false, false ) );
$fontello = trailingslashit( $root ) . 'fontello/';
$icomoon = trailingslashit( $root ) . 'icomoon/';
$uploads = trailingslashit( wp_upload_dir( null, false )['basedir'] ) . 'elementor/custom-icons';
$destinations = [];
$checks = [];
wp_mkdir_p( $fontello . 'css/' );
wp_mkdir_p( $fontello . 'font/' );
wp_mkdir_p( $icomoon . 'fonts/' );
wp_mkdir_p( $icomoon . 'demo-files/' );
$filesystem = \ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons::get_wp_filesystem();

try {
	$fontello_name = $slug . '-fontello';
	file_put_contents( $fontello . 'config.json', wp_json_encode( [
		'name' => $fontello_name,
		'css_prefix_text' => 'icon-',
		'glyphs' => [ [ 'css' => 'star', 'code' => 0xe801 ] ],
	] ) );
	file_put_contents( $fontello . 'README.txt', 'synthetic' );
	file_put_contents( $fontello . 'LICENSE.txt', 'synthetic' );
	file_put_contents( $fontello . 'demo.html', '<script>untrusted</script>' );
	file_put_contents( $fontello . 'font/' . $fontello_name . '.woff', 'test-only-woff' );
	file_put_contents( $fontello . 'css/' . $fontello_name . '.css',
		'@font-face {font-family:"' . $fontello_name . '";'
		. 'src:url("../font/' . $fontello_name . '.woff?code=30") format("woff");}' . "\n"
		. '.icon-star:before {content:"\e801";}' );
	$fontello_class = '\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets\Fontello';
	$handler = new $fontello_class( $fontello );
	$checks['fontello_export_has_expected_directories'] = $handler->is_icon_set();
	$checks['fontello_css_and_icon_data_safe_before_import'] =
		true === $handler->validate_name();
	$handler->handle_new_icon_set();
	$checks['fontello_validates_css_data_and_local_font'] =
		true === $handler->validate_icon_contents()
		&& true === $handler->validate_public_icon_assets();
	$handler->move_files( 0 );
	$config = $handler->build_config();
	$destination = trailingslashit( $uploads ) . $config['name'];
	$destinations[] = $destination;
	$checks['fontello_icon_config_and_font_published_without_demo_html'] =
		'fontello' === strtolower( $config['custom_icon_type'] )
		&& in_array( 'star', $config['icons'], true )
		&& file_exists( $destination . '/font/' . $fontello_name . '.woff' )
		&& file_exists( $destination . '/css/' . $fontello_name . '.css' )
		&& ! file_exists( $destination . '/demo.html' );

	$icomoon_name = $slug . '-icomoon';
	file_put_contents( $icomoon . 'selection.json', wp_json_encode( [
		'metadata' => [ 'name' => $icomoon_name ],
		'preferences' => [ 'fontPref' => [
			'prefix' => 'icon-', 'classSelector' => '.icon'
		] ],
		'icons' => [ [ 'properties' => [ 'name' => 'star', 'code' => 0xe801 ] ] ],
	] ) );
	file_put_contents( $icomoon . 'demo.html', '<script>untrusted</script>' );
	file_put_contents( $icomoon . 'Read Mw.txt', 'synthetic' );
	file_put_contents( $icomoon . 'demo-files/notes.txt', 'synthetic' );
	file_put_contents( $icomoon . 'fonts/icomoon.woff', 'test-only-woff' );
	file_put_contents( $icomoon . 'style.css',
		'@font-face {font-family:"icomoon";'
		. 'src:url("fonts/icomoon.woff?v=1") format("woff");}' . "\n"
		. '.icon-star:before {content:"\e801";}' );
	$icomoon_class = '\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets\Icomoon';
	$handler = new $icomoon_class( $icomoon );
	$checks['icomoon_export_has_expected_directories'] = $handler->is_icon_set();
	$checks['icomoon_pack_name_safe'] = true === $handler->validate_name();
	$handler->handle_new_icon_set();
	$checks['icomoon_validates_css_data_and_local_font'] =
		true === $handler->validate_icon_contents()
		&& true === $handler->validate_public_icon_assets();
	$handler->move_files( 0 );
	$config = $handler->build_config();
	$destination = trailingslashit( $uploads ) . $config['name'];
	$destinations[] = $destination;
	$checks['icomoon_icon_config_and_font_published_without_demo_html'] =
		'icomoon' === strtolower( $config['custom_icon_type'] )
		&& in_array( 'star', $config['icons'], true )
		&& file_exists( $destination . '/fonts/icomoon.woff' )
		&& file_exists( $destination . '/style.css' )
		&& ! file_exists( $destination . '/demo.html' );
} finally {
	// Refuse to remove arbitrary directories: only our random test names
	// directly under this disposable WordPress's custom icon root.
	$root_real = realpath( $uploads );
	foreach ( $destinations as $dir ) {
		$real = realpath( $dir );
		if ( $root_real && $real && ! is_link( $real )
			&& dirname( $real ) === $root_real
			&& str_starts_with( basename( $real ), $slug ) ) {
			$filesystem->rmdir( $real, true );
		}
	}
	$root_tmp = realpath( $root );
	if ( $root_tmp && str_starts_with( basename( $root_tmp ), 'zmp-icon-formats-' )
		&& dirname( $root_tmp ) === realpath( sys_get_temp_dir() ) ) {
		$filesystem->rmdir( $root_tmp, true );
	}
}
foreach ( $checks as $name => $passed ) {
	echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) !== 8 || in_array( false, $checks, true ) ) {
	fwrite( STDERR, 'FAILED_ICON_FORMATS: ' . wp_json_encode(
		array_keys( array_filter( $checks, static function ( $passed ) { return true !== $passed; } ) )
	) . PHP_EOL );
	exit( 4 );
}
