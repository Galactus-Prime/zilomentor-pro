<?php
/**
 * Isolated only: prove external MU guard blocks vendor overwrite attempts
 * while leaving other plugins and vulnerability scanners untouched.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
    exit( 2 );
}
$guard = WP_PLUGIN_DIR . '/elementor-pro/tools/zmp-release-guard.php';
if ( ! is_file( $guard ) ) {
    fwrite( STDERR, "Independent external MU guard fixture missing\n" );
    exit( 3 );
}
require_once $guard;

$compat = [ 'type' => 'plugin', 'action' => 'update', 'plugin' => 'elementor-pro/elementor-pro.php' ];
$other = [ 'type' => 'plugin', 'action' => 'update', 'plugin' => 'woocommerce/woocommerce.php' ];
$source = WP_PLUGIN_DIR . '/elementor-pro';
$normal_source = WP_PLUGIN_DIR . '/elementor';

$checks = [
    'recognises_zilomentor_by_independent_header' => zmp_release_guard_active(),
    'blocks_targeted_plugin_upgrade' => is_wp_error( apply_filters( 'upgrader_pre_install', true, $compat ) ),
    'blocks_targeted_remote_download' => is_wp_error( apply_filters( 'upgrader_pre_download', false, 'https://example.invalid/wp-plugin.zip', (object) [], $compat ) ),
    'blocks_vague_installer_overwriting_compat_directory' => is_wp_error( apply_filters( 'upgrader_source_selection', $source, $source, (object) [], [ 'type' => 'plugin', 'action' => 'install' ] ) ),
    'blocks_auto_update_for_zilomentor' => false === apply_filters( 'auto_update_plugin', true, (object) [ 'plugin' => 'elementor-pro/elementor-pro.php' ] ),
    'allows_other_plugin_upgrade' => true === apply_filters( 'upgrader_pre_install', true, $other ),
    'allows_other_plugin_download' => false === apply_filters( 'upgrader_pre_download', false, 'https://example.invalid/woo.zip', (object) [], $other ),
    'allows_other_plugin_source' => $normal_source === apply_filters( 'upgrader_source_selection', $normal_source, $normal_source, (object) [], [ 'type' => 'plugin', 'action' => 'install' ] ),
    'allows_other_plugin_auto_update' => true === apply_filters( 'auto_update_plugin', true, (object) [ 'plugin' => 'woocommerce/woocommerce.php' ] ),
];
foreach ( $checks as $name => $pass ) {
    echo ( $pass ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
exit( in_array( false, $checks, true ) ? 4 : 0 );
