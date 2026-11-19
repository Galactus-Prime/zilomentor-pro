<?php
/**
 * Force a missing global post during a synthetic Posts widget REST preview.
 * Requires disposable WordPress and an isolated Docker network.
 */
if ( ! defined( 'ABSPATH' ) || getenv( 'ZMP_ISOLATED_QA' ) !== 'yes' ) {
    exit( 2 );
}
$widget = \Elementor\Plugin::instance()->widgets_manager->get_widget_types( 'posts' );
if ( ! $widget ) {
    fwrite( STDERR, "Posts widget not registered\n" );
    exit( 3 );
}
$original_post = $GLOBALS['post'] ?? null;
$original_uri = $_SERVER['REQUEST_URI'] ?? null;
$original_ref = $_SERVER['HTTP_REFERER'] ?? null;
$GLOBALS['post'] = null;
$_SERVER['REQUEST_URI'] = '/wp-json/wp/v2/posts';
$_SERVER['HTTP_REFERER'] = 'http://web:8080/zmp-qa-intentionally-no-post/';
$warnings = [];
set_error_handler( function( $severity, $message ) use ( &$warnings ) {
    if ( E_WARNING === $severity || E_NOTICE === $severity ) {
        $warnings[] = substr( $message, 0, 180 );
    }
    return false;
} );
try {
    $result = $widget->get_wp_link_page( 2 );
    $expected = esc_url( get_pagenum_link( 2 ) );
} finally {
    restore_error_handler();
    $GLOBALS['post'] = $original_post;
    if ( null === $original_uri ) {
        unset( $_SERVER['REQUEST_URI'] );
    } else {
        $_SERVER['REQUEST_URI'] = $original_uri;
    }
    if ( null === $original_ref ) {
        unset( $_SERVER['HTTP_REFERER'] );
    } else {
        $_SERVER['HTTP_REFERER'] = $original_ref;
    }
}
$passed = is_string( $result ) && '' !== $result && $result === $expected && ! $warnings;
echo wp_json_encode( [
    'passed' => $passed,
    'expected_fallback_used' => $result === $expected,
    'warning_count' => count( $warnings ),
] );
exit( $passed ? 0 : 4 );
