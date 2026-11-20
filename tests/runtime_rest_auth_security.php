<?php
/**
 * Synthetic REST capability regression for privileged ElementorPro routes.
 *
 * Never dispatch endpoint callbacks or trigger actual writes. Check only the
 * permission callbacks installed in a disposable WordPress environment.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
    exit( 2 );
}

$server = rest_get_server();
$routes = $server->get_routes();
$targets = [
    '/elementor-pro/v1/custom-icon-svg' => [ 'GET' ],
    '/elementor-pro/v1/font-awesome-pro-icon' => [ 'GET', 'POST' ],
];

// Atomic icon routes may be feature-gated on a fresh website. Register
// their *actual* implementations in this synthetic REST server if needed,
// so access-control tests do not silently disappear when V4 is disabled.
$optional_classes = [
    '/elementor-pro/v1/custom-icon-svg' =>
        '\\ElementorPro\\Modules\\AtomicCustomIcons\\Rest_Api',
    '/elementor-pro/v1/font-awesome-pro-icon' =>
        '\\ElementorPro\\Modules\\AtomicCustomIcons\\Font_Awesome_Pro_Rest_Api',
];
foreach ( $optional_classes as $route => $class ) {
    if ( ! isset( $routes[ $route ] ) && class_exists( $class ) ) {
        $api = new $class();
        $register = new \ReflectionMethod( $api, 'register_routes' );
        $register->invoke( $api );
        $routes = $server->get_routes();
    }
}

$checks = [];
$original_id = get_current_user_id();
$user_ids = [];

$create_role = static function ( string $role ) use ( &$user_ids ) {
    $name = 'zmp-only-qa-' . $role . '-' . wp_generate_password( 9, false );
    $id = wp_create_user( $name, wp_generate_password( 28, true ), '' );
    if ( is_wp_error( $id ) ) {
        throw new \RuntimeException( 'Failed to create disposable role fixture' );
    }
    $user_ids[] = $id;
    $user = new \WP_User( $id );
    $user->set_role( $role );
    return $id;
};

try {
    $users = [
        'guest' => 0,
        'subscriber' => $create_role( 'subscriber' ),
        'contributor' => $create_role( 'contributor' ),
        'editor' => $create_role( 'editor' ),
    ];
    $tested_routes = 0;
    foreach ( $targets as $route => $methods ) {
        if ( ! isset( $routes[ $route ] ) ) {
            // A truly missing API cannot be claimed as covered.
            echo 'SKIP missing_optional_route ' . $route . PHP_EOL;
            continue;
        }
        foreach ( $methods as $method ) {
            $handler = null;
            foreach ( $routes[ $route ] as $registered ) {
                if ( ! is_array( $registered ) || ! isset( $registered['methods'] ) ) {
                    continue;
                }
                $registered_methods = $registered['methods'];
                if ( is_string( $registered_methods ) ) {
                    $registered_methods = explode( ',', $registered_methods );
                }
                if ( ! is_array( $registered_methods ) ||
                    ! in_array( $method, array_map( 'strtoupper', $registered_methods ), true ) ) {
                    continue;
                }
                if ( is_callable( $registered['permission_callback'] ?? null ) ) {
                    $handler = $registered['permission_callback'];
                    break;
                }
            }
            $id = preg_replace( '/[^a-z0-9]+/i', '_', $route . '_' . $method );
            $checks[ $id . '_has_permission_callback' ] = null !== $handler;
            if ( null === $handler ) {
                continue;
            }
            $tested_routes++;
            $request = new \WP_REST_Request( $method, $route );
            $request->set_param( 'library', 'synthetic-qa' );
            $request->set_param( 'value', 'synthetic-icon' );
            foreach ( $users as $role => $user_id ) {
                wp_set_current_user( $user_id );
                $granted = call_user_func( $handler, $request );
                $allowed = true === $granted;
                if ( in_array( $role, [ 'guest', 'subscriber' ], true )
                    || ( 'POST' === $method && 'contributor' === $role ) ) {
                    $checks[ $id . '_rejects_' . $role ] = ! $allowed;
                }
                if ( 'GET' === $method && 'editor' === $role ) {
                    $checks[ $id . '_allows_editor' ] = $allowed;
                }
            }
        }
    }
    $checks['tested_registered_routes'] = $tested_routes >= 2;
} finally {
    wp_set_current_user( $original_id );
    if ( ! function_exists( 'wp_delete_user' ) ) {
        require_once ABSPATH . 'wp-admin/includes/user.php';
    }
    foreach ( $user_ids as $id ) {
        wp_delete_user( $id );
    }
}

foreach ( $checks as $label => $passed ) {
    echo ( $passed ? 'PASS ' : 'FAIL ' ) . $label . PHP_EOL;
}
if ( ! $checks || in_array( false, $checks, true ) ) {
    exit( 4 );
}
