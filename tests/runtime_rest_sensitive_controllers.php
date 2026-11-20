<?php
/**
 * Verify low-privilege access to sensitive Elementor Pro controller data.
 * Synthetic WordPress only. Invoke permission callbacks, not REST handlers.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}

$classes = [
	'submissions' => '\\ElementorPro\\Modules\\Forms\\Submissions\\Data\\Controller',
	'submission_forms' => '\\ElementorPro\\Modules\\Forms\\Submissions\\Data\\Forms_Controller',
	'global_templates' => '\\ElementorPro\\Modules\\GlobalWidget\\Data\\Controller',
	'notes' => '\\ElementorPro\\Modules\\Notes\\Data\\Controller',
];
$controllers = [];
foreach ( $classes as $label => $class ) {
	if ( ! class_exists( $class ) ) {
		fwrite( STDERR, "Sensitive controller missing: $label\n" );
		exit( 3 );
	}
	$controllers[ $label ] = ( new \ReflectionClass( $class ) )->newInstanceWithoutConstructor();
}

// Ability registration already declares capabilities; these tests also call
// the public execute() methods directly so protection cannot be bypassed by
// another integration invoking them outside WordPress' Abilities registry.
$mcp_classes = [
	'mcp_read_submissions' => '\ElementorPro\Modules\Mcp\Abilities\List_Form_Submissions_Ability',
	'mcp_write_submissions' => '\ElementorPro\Modules\Mcp\Abilities\Manage_Form_Submissions_Ability',
	'mcp_store_settings' => '\ElementorPro\Modules\Mcp\Abilities\Manage_Woocommerce_Settings_Ability',
];
$mcp_abilities = [];
foreach ( $mcp_classes as $label => $class ) {
	if ( ! class_exists( $class ) ) {
		fwrite( STDERR, "Sensitive MCP ability missing: $label\\n" );
		exit( 3 );
	}
	$mcp_abilities[ $label ] = new $class();
}

$old_user = get_current_user_id();
$ids = [];
$checks = [];
try {
	foreach ( [ 'subscriber', 'contributor', 'editor', 'administrator' ] as $role ) {
		$login = 'zmp-sensitive-qa-' . $role . '-' . wp_generate_password( 8, false );
		$id = wp_create_user( $login, wp_generate_password( 20, true ), '' );
		if ( is_wp_error( $id ) ) {
			throw new \RuntimeException( 'Could not create synthetic user' );
		}
		( new \WP_User( $id ) )->set_role( $role );
		$ids[ $role ] = $id;
	}
	$users = [ 'guest' => 0 ] + $ids;
	$request = new \WP_REST_Request( 'GET', '/elementor-pro/v1/form-submissions' );
	foreach ( $users as $role => $id ) {
		wp_set_current_user( $id );
		foreach ( [ 'submissions', 'submission_forms' ] as $label ) {
			$result = $controllers[ $label ]->get_permission_callback( $request );
			$checks[ $label . '_' . $role ] = ( $role === 'administrator' ) === ( true === $result );
		}
		// These three methods must independently deny all low-privilege
		// accounts before reading PII or altering any store configuration.
		if ( 'administrator' !== $role ) {
			foreach ( $mcp_abilities as $label => $ability ) {
				$result = $ability->execute( [ 'action' => 'get' ] );
				$checks[ $label . '_' . $role . '_direct_execution_denied' ] =
					is_wp_error( $result ) && 'rest_forbidden' === $result->get_error_code();
			}
		} else {
			$checks['mcp_admin_has_manage_options'] = current_user_can( 'manage_options' );
		}
		$global_allowed = $controllers['global_templates']->get_permission_callback( $request );
		$checks[ 'global_templates_' . $role ] =
			( in_array( $role, [ 'contributor', 'editor', 'administrator' ], true ) ) === ( true === $global_allowed );

		// Notes may carry comments about internal drafts and collaborators.
		// Anonymous and subscriber access must be denied for every method.
		if ( in_array( $role, [ 'guest', 'subscriber' ], true ) ) {
			foreach ( [ 'GET', 'POST', 'PATCH', 'DELETE' ] as $method ) {
				$request->set_method( $method );
				$request->set_param( 'id', 0 );
				$request->set_param( 'parent_id', 0 );
				$checks[ 'notes_' . $role . '_' . strtolower( $method ) ] =
					false === $controllers['notes']->get_permission_callback( $request );
			}
			$request->set_method( 'GET' );
		}
	}

	// Positive privileged-path checks remain read-only or deliberately invalid.
	wp_set_current_user( $ids['administrator'] );
	$checks['mcp_admin_may_list_submissions'] =
		is_array( $mcp_abilities['mcp_read_submissions']->execute( [] ) );
	$checks['mcp_admin_may_read_store_settings'] =
		is_array( $mcp_abilities['mcp_store_settings']->execute( [ 'action' => 'get' ] ) );
	$invalid_update = $mcp_abilities['mcp_write_submissions']->execute( [ 'operations' => [] ] );
	$checks['mcp_admin_reaches_validation_not_permission_denial'] =
		is_wp_error( $invalid_update ) && 'invalid_input' === $invalid_update->get_error_code();

	// WooCommerce's shop_manager may manage store page mappings, but must
	// never gain access to private form submissions via that Woo capability.
	$shop_user = wp_create_user(
		'zmp-mcp-shop-' . wp_generate_password( 8, false ),
		wp_generate_password( 20, true ), ''
	);
	if ( is_wp_error( $shop_user ) ) {
		throw new \RuntimeException( 'Could not create synthetic shop manager' );
	}
	( new \WP_User( $shop_user ) )->set_role( 'shop_manager' );
	$ids['shop_manager'] = $shop_user;
	wp_set_current_user( $shop_user );
	$checks['mcp_shop_manager_can_read_store_pages'] =
		is_array( $mcp_abilities['mcp_store_settings']->execute( [ 'action' => 'get' ] ) );
	foreach ( [ 'mcp_read_submissions', 'mcp_write_submissions' ] as $label ) {
		$denied = $mcp_abilities[ $label ]->execute( [] );
		$checks[ $label . '_shop_manager_denied' ] =
			is_wp_error( $denied ) && 'rest_forbidden' === $denied->get_error_code();
	}
} finally {
	wp_set_current_user( $old_user );
	if ( ! function_exists( 'wp_delete_user' ) ) {
		require_once ABSPATH . 'wp-admin/includes/user.php';
	}
	foreach ( $ids as $id ) {
		wp_delete_user( $id );
	}
}

foreach ( $checks as $name => $ok ) {
	echo ( $ok ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) < 20 || in_array( false, $checks, true ) ) {
	exit( 4 );
}
