<?php
/**
 * Disposable runtime regression for ZiloMentor/Vamtam plugin load order.
 * The independent plugin must register its plugins_loaded callback BEFORE
 * the alphabetically earlier Vamtam integration plugin.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
    exit( 2 );
}

global $wp_filter;
$callbacks = isset( $wp_filter['plugins_loaded'] )
    ? $wp_filter['plugins_loaded']->callbacks
    : array();
$ordered = array();
ksort( $callbacks, SORT_NUMERIC );
foreach ( $callbacks as $priority => $events ) {
    foreach ( $events as $event ) {
        $callback = $event['function'] ?? null;
        if ( 'pro_elements_plugin_load_plugin' === $callback ) {
            $ordered[] = 'zmp';
        } elseif ( is_array( $callback ) && isset( $callback[0], $callback[1] )
            && is_object( $callback[0] )
            && 'VamtamElementorIntregration' === get_class( $callback[0] )
            && 'init' === $callback[1] ) {
            $ordered[] = 'vamtam';
        }
    }
}

$active = (array) get_option( 'active_plugins', array() );
$independent = in_array( 'zilomentor-pro/elementor-pro.php', $active, true );
$legacy = in_array( 'elementor-pro/elementor-pro.php', $active, true );
$zmp_index = array_search( 'zmp', $ordered, true );
$vamtam_index = array_search( 'vamtam', $ordered, true );
$checks = array(
    'single_zilomentor_instance' => defined( 'ZILOMENTOR_VERSION' ) &&
        '0.1.2' === ZILOMENTOR_VERSION,
    'elementor_core_loaded' => did_action( 'elementor/loaded' ) > 0,
    'compatibility_API_active' => defined( 'ELEMENTOR_PRO_VERSION' ) &&
        class_exists( '\\ElementorPro\\Plugin' ),
    'vamtam_callbacks_register_after_zilomentor' =>
        false !== $zmp_index && false !== $vamtam_index &&
        $zmp_index < $vamtam_index,
    'early_loader_only_for_independent_identity' =>
        $independent ? ( defined( 'ZMP_EARLY_COMPAT_BOOTSTRAP' ) &&
            'yes' === ZMP_EARLY_COMPAT_BOOTSTRAP ) :
            ( $legacy && ! defined( 'ZMP_EARLY_COMPAT_BOOTSTRAP' ) ),
);
foreach ( $checks as $name => $ok ) {
    echo ( $ok ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
exit( in_array( false, $checks, true ) ? 4 : 0 );
