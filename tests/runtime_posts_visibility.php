<?php
/**
 * Posts-widget read authorization regression, disposable WordPress only.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
    exit( 2 );
}
$class = '\\ElementorPro\\Modules\\Posts\\Data\\Controller';
if ( ! class_exists( $class ) ) {
    fwrite( STDERR, "Posts controller missing\n" );
    exit( 3 );
}
$controller = ( new \ReflectionClass( $class ) )->newInstanceWithoutConstructor();

$create = static function ( $status, $password = '' ) {
    $id = wp_insert_post( [
        'post_type' => 'page',
        'post_title' => 'ZiloMentor synthetic Posts ' . $status,
        'post_status' => $status,
        'post_password' => $password,
    ], true );
    if ( is_wp_error( $id ) || ! $id ) {
        throw new \RuntimeException( 'Could not create disposable document' );
    }
    return (int) $id;
};
$published = $create( 'publish' );
$private = $create( 'private' );
$draft = $create( 'draft' );
$protected = $create( 'publish', wp_generate_password( 20, false ) );
$old_user = get_current_user_id();
$checks = [];
try {
    $request = new \WP_REST_Request( 'GET', '/elementor-pro/v1/posts-widget' );
    wp_set_current_user( 0 );

    foreach ( [
        'published' => [ $published, true ],
        'private' => [ $private, false ],
        'draft' => [ $draft, false ],
        'password_protected' => [ $protected, false ],
        'missing' => [ PHP_INT_MAX, false ],
        'invalid' => [ 0, false ],
    ] as $name => $case ) {
        $request->set_param( 'post_id', $case[0] );
        $checks[ 'guest_posts_' . $name ] =
            $case[1] === $controller->get_permission_callback( $request );
    }

    $name = 'zmp-posts-qa-' . wp_generate_password( 10, false );
    $user = wp_create_user( $name, wp_generate_password( 22, true ), '' );
    if ( is_wp_error( $user ) ) {
        throw new \RuntimeException( 'Could not create synthetic subscriber' );
    }
    try {
        ( new \WP_User( $user ) )->set_role( 'subscriber' );
        wp_set_current_user( $user );
        $request->set_param( 'post_id', $draft );
        $checks['subscriber_cannot_preview_draft'] =
            false === $controller->get_permission_callback( $request );
        $request->set_param( 'post_id', $private );
        $checks['subscriber_cannot_preview_private'] =
            false === $controller->get_permission_callback( $request );
        $request->set_param( 'post_id', $published );
        $checks['subscriber_can_view_public_posts_pagination'] =
            true === $controller->get_permission_callback( $request );
    } finally {
        if ( ! function_exists( 'wp_delete_user' ) ) {
            require_once ABSPATH . 'wp-admin/includes/user.php';
        }
        wp_delete_user( $user );
    }
    // In editor context, the active WordPress admin may edit their drafts.
    $admins = get_users( [ 'role' => 'administrator', 'number' => 1, 'fields' => 'ID' ] );
    if ( $admins ) {
        wp_set_current_user( (int) $admins[0] );
        $request->set_param( 'post_id', $draft );
        $checks['admin_can_edit_draft_posts_widget'] =
            true === $controller->get_permission_callback( $request );
    }
} finally {
    wp_set_current_user( $old_user );
    foreach ( [ $published, $private, $draft, $protected ] as $id ) {
        wp_delete_post( $id, true );
    }
}

foreach ( $checks as $name => $passed ) {
    echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) < 9 || in_array( false, $checks, true ) ) {
    exit( 4 );
}
