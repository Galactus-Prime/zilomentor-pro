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
    $rest_routed = $widget->is_rest_request();
    $result = $widget->get_wp_link_page( 2 );
    $expected = esc_url( get_pagenum_link( 2 ) );

    // Exercise the Full Content skin separately: a preview can call it with
    // no current WP_Post. The old code accessed $post->ID immediately.
    $skin = new class {
        use \ElementorPro\Modules\Posts\Skins\Skin_Content_Base;
    };
    ob_start();
    try {
        $skin->render_post_content();
    } finally {
        $missing_post_content = ob_get_clean();
    }
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
$passed = $rest_routed && is_string( $result ) && '' !== $result
    && $result === $expected && '' === $missing_post_content && ! $warnings;
echo wp_json_encode( [
    'passed' => $passed,
    'rest_preview_path_exercised' => $rest_routed,
    'expected_fallback_used' => $result === $expected,
    'warning_count' => count( $warnings ),
    'missing_post_full_content_empty' => '' === $missing_post_content,
] );
exit( $passed ? 0 : 4 );
