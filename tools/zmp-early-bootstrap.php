<?php
/**
 * Plugin Name: ZiloMentor Early Compatibility Bootstrap
 * Description: Preserves Elementor Pro compatibility init order when ZiloMentor is installed in its independent plugin folder.
 * Version: 0.1.0
 *
 * Install independently at wp-content/mu-plugins/zmp-early-bootstrap.php.
 * Not part of the independent plugin ZIP. No database writes, updates,
 * requests, or privileged actions. Remains inert on the legacy folder.
 *
 * WordPress loads root-level must-use plugins before ordinary active plugins.
 * Vamtam Elementor Integration installs its plugins_loaded callback while
 * its regular plugin file is being included. Without this adapter, the new
 * alphabetically later zilomentor-pro directory can register Elementor Pro
 * after Vamtam and alter CSS/template initialization order.
 *
 * This adapter only includes the *already activated* ZiloMentor bootstrap
 * early enough to register its normal, guarded plugins_loaded callback.
 * WordPress' normal include_once skips the same file on the later load.
 */
if ( ! defined( 'ABSPATH' ) || ! defined( 'WP_PLUGIN_DIR' ) ) {
    return;
}

$zmp_independent_basename = 'zilomentor-pro/elementor-pro.php';
$zmp_legacy_basename = 'elementor-pro/elementor-pro.php';
$zmp_active_plugins = (array) get_option( 'active_plugins', array() );
if ( ! in_array( $zmp_independent_basename, $zmp_active_plugins, true )
    || in_array( $zmp_legacy_basename, $zmp_active_plugins, true ) ) {
    unset( $zmp_independent_basename, $zmp_legacy_basename, $zmp_active_plugins );
    return;
}

$zmp_entrypoint = WP_PLUGIN_DIR . '/' . $zmp_independent_basename;
if ( ! is_file( $zmp_entrypoint ) || is_link( $zmp_entrypoint )
    || ! function_exists( 'get_file_data' ) ) {
    unset( $zmp_independent_basename, $zmp_legacy_basename, $zmp_active_plugins, $zmp_entrypoint );
    return;
}
$zmp_headers = get_file_data(
    $zmp_entrypoint,
    array( 'Name' => 'Plugin Name', 'UpdateURI' => 'Update URI' )
);
if ( ( $zmp_headers['Name'] ?? '' ) !== 'ZiloMentor Pro'
    || ( $zmp_headers['UpdateURI'] ?? '' ) !== 'https://github.com/Galactus-Prime/zilomentor-pro' ) {
    unset( $zmp_independent_basename, $zmp_legacy_basename, $zmp_active_plugins, $zmp_entrypoint, $zmp_headers );
    return;
}

// Only an activated, verified local independent ZiloMentor installation is
// eligible for this compatibility ordering adapter.
if ( ! defined( 'ZMP_EARLY_COMPAT_BOOTSTRAP' ) ) {
    define( 'ZMP_EARLY_COMPAT_BOOTSTRAP', 'yes' );
}
require_once $zmp_entrypoint;

unset( $zmp_independent_basename, $zmp_legacy_basename, $zmp_active_plugins, $zmp_entrypoint, $zmp_headers );
