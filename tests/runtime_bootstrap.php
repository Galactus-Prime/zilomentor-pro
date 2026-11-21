<?php
/**
 * Read-only WP-CLI smoke test. Usage: wp eval-file tests/runtime_bootstrap.php
 *
 * Run only on a disposable staging WordPress environment with free Elementor
 * and ZiloMentor Pro activated. No production data or settings are modified.
 */
if ( ! defined( 'ABSPATH' ) ) {
    exit( 2 );
}

$checks = [
    'free Elementor loaded' => did_action( 'elementor/loaded' ) > 0,
    'ZiloMentor Pro included' => defined( 'ZILOMENTOR_VERSION' ),
    'Elementor Pro API version' => defined( 'ELEMENTOR_PRO_VERSION' ),
    'ElementorPro plugin class available' => class_exists( 'ElementorPro\\Plugin' ),
    'Elementor theme location helper' => function_exists( 'elementor_theme_do_location' ),
];
$failed = 0;
foreach ( $checks as $name => $passed ) {
    echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
    $failed += $passed ? 0 : 1;
}
echo 'RESULT: ' . ( $failed ? 'FAIL' : 'PASS' ) . PHP_EOL;
if ( $failed ) {
    exit( 1 );
}
