<?php
/**
 * Actual disposable WordPress custom-icon import asset security regressions.
 * Legacy webfont SVG is deliberately supported using strict inert markup;
 * active same-origin SVG, CSS imports/remote references and local traversal
 * must not reach public uploads.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}
$class = '\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets\Fontastic';
$source = trailingslashit( sys_get_temp_dir() ) . 'zmp-icon-active-'
	. strtolower( wp_generate_password( 10, false, false ) );
wp_mkdir_p( trailingslashit( $source ) . 'fonts' );
$stylesheet = trailingslashit( $source ) . 'styles.css';
$svgfile = trailingslashit( $source ) . 'fonts/dummy.svg';
$good_svg = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">'
	. '<defs><font id="safe-font" horiz-adv-x="1000">'
	. '<font-face font-family="ZMP Safe Font" units-per-em="1000" ascent="800" descent="-200"/>'
	. '<missing-glyph horiz-adv-x="500"/>'
	. '<glyph glyph-name="star" unicode="&#xe801;" horiz-adv-x="500" d="M0 0L10 10Z"/>'
	. '</font></defs></svg>';
$base_css = '@font-face{font-family:"zmp-safe";'
	. 'src:url("fonts/dummy.woff?ver=1") format("woff"),'
	. 'url("fonts/dummy.svg#safe-font") format("svg");}'
	. '[class^="zmp-"] {font-family:"zmp-safe";}'
	. '.zmp-star:before {content:"\ea01";}';
$checks = [];
try {
	file_put_contents( $stylesheet, $base_css );
	file_put_contents( $svgfile, $good_svg );
	file_put_contents( trailingslashit( $source ) . 'fonts/dummy.woff', 'dummy-font-test-only' );
	file_put_contents( trailingslashit( $source ) . 'icons-reference.html', 'synthetic-only' );
	$icon = new $class( trailingslashit( $source ) );
	$icon->handle_new_icon_set();
	$checks['valid_local_css_and_inert_svg_webfont_allowed'] =
		true === $icon->validate_icon_contents()
		&& true === $icon->validate_public_icon_assets();

	$css_attacks = [
		'remote_css_import' => '@import url("https://remote.invalid/payload.css");',
		'remote_font_reference' => '@font-face{src:url(https://remote.invalid/font.woff);}',
		'css_data_url' => 'a{background:url(data:text/html,%3Cscript%3E);}',
		'css_javascript_url' => 'a{background:url(javascript:alert(1));}',
		'css_traversal_reference' => '@font-face{src:url(../../../wp-config.php);}',
		'css_missing_font' => '@font-face{src:url(fonts/missing.woff);}',
		'css_escaped_url' => 'a{background:url(https\3a //remote.invalid/a.woff);}',
		'css_style_binding' => 'a{-moz-binding:url(fonts/dummy.woff);}',
	];
	foreach ( $css_attacks as $name => $payload ) {
		file_put_contents( $stylesheet, $base_css . "\n" . $payload );
		$checks[ 'refuses_' . $name ] = is_wp_error( $icon->validate_public_icon_assets() );
	}
	file_put_contents( $stylesheet, $base_css );

	$svg_attacks = [
		'script_element' => str_replace( '<defs>', '<script>alert(1)</script><defs>', $good_svg ),
		'foreign_object' => str_replace( '<defs>', '<foreignObject><body xmlns="http://www.w3.org/1999/xhtml">Unsafe</body></foreignObject><defs>', $good_svg ),
		'event_handler' => str_replace( 'id="safe-font"', 'id="safe-font" onload="alert(1)"', $good_svg ),
		'remote_url_attribute' => str_replace( 'id="safe-font"', 'id="safe-font" href="https://remote.invalid/"', $good_svg ),
		'active_style_attribute' => str_replace( 'id="safe-font"', 'id="safe-font" style="color:red"', $good_svg ),
		'doctype_entity' => '<!DOCTYPE svg [<!ENTITY payload SYSTEM "file:///etc/passwd">]>' . $good_svg,
		'graphics_nonfont' => '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>',
		'non_svg_document' => '<html><script>alert(1)</script></html>',
	];
	foreach ( $svg_attacks as $name => $payload ) {
		file_put_contents( $svgfile, $payload );
		$checks[ 'refuses_' . $name ] = is_wp_error( $icon->validate_public_icon_assets() );
	}
	file_put_contents( $svgfile, $good_svg );
	$checks['restoring_valid_assets_restores_acceptance'] =
		true === $icon->validate_public_icon_assets();
} finally {
	// Only this generated disposable source is eligible for deletion.
	$parent = realpath( dirname( $source ) );
	$resolved = realpath( $source );
	if ( false !== $parent && false !== $resolved
		&& dirname( $resolved ) === $parent
		&& str_starts_with( basename( $resolved ), 'zmp-icon-active-' ) ) {
		\ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons::get_wp_filesystem()
			->rmdir( $resolved, true );
	}
}
foreach ( $checks as $name => $passed ) {
	echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) !== 18 || in_array( false, $checks, true ) ) {
	exit( 4 );
}
