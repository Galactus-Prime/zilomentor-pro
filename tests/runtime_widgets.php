<?php
/**
 * Staging-only, read-only widget registry regression.
 * Run with: wp eval-file wp-content/plugins/elementor-pro/tests/runtime_widgets.php
 * Requires free Elementor and ZiloMentor Pro active in disposable WordPress.
 */
if ( ! defined( 'ABSPATH' ) ) {
    exit( 2 );
}

if ( ! class_exists( 'Elementor\\Plugin' ) || ! class_exists( 'ElementorPro\\Plugin' ) ) {
    echo 'FAIL Elementor / ElementorPro bootstrap missing' . PHP_EOL;
    exit( 1 );
}

$types = \Elementor\Plugin::instance()->widgets_manager->get_widget_types();
$required = [ 'form', 'nav-menu', 'posts', 'theme-site-logo' ];
if ( class_exists( 'WooCommerce' ) ) {
    $required[] = 'woocommerce-menu-cart';
}

$failed = 0;
foreach ( $required as $name ) {
    $ok = isset( $types[ $name ] );
    echo ( $ok ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
    $failed += $ok ? 0 : 1;
}
echo 'Total registered Elementor widgets: ' . count( $types ) . PHP_EOL;
echo 'RESULT: ' . ( $failed ? 'FAIL' : 'PASS' ) . PHP_EOL;
if ( $failed ) {
    exit( 1 );
}
