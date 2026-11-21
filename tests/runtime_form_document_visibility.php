<?php
/**
 * Form submission target-document authorization regression.
 * Runs only in disposable WordPress. No HTTP forms, email or production data.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
    exit( 2 );
}

$utils = '\ElementorPro\Core\Utils';
$atomic_class = '\ElementorPro\Modules\AtomicForm\Atomic_Form_Controller';
$checks = [];
$created = [];
$old_user = get_current_user_id();
$editor_id = wp_create_user(
    'zmp-doc-qa-' . wp_generate_password( 9, false ),
    wp_generate_password( 24, true ),
    ''
);
if ( is_wp_error( $editor_id ) ) {
    exit( 3 );
}
( new \WP_User( $editor_id ) )->set_role( 'editor' );

try {
    $fixtures = [
        'published' => [ 'post_status' => 'publish' ],
        'draft' => [ 'post_status' => 'draft' ],
        'private' => [ 'post_status' => 'private' ],
        'protected' => [ 'post_status' => 'publish', 'post_password' => 'qa-secret' ],
        'trash' => [ 'post_status' => 'trash' ],
    ];
    foreach ( $fixtures as $name => $args ) {
        $id = wp_insert_post( array_merge( [
            'post_type' => 'page',
            'post_title' => 'ZMP isolated Form ' . $name,
            'post_author' => $editor_id,
        ], $args ), true );
        if ( is_wp_error( $id ) || ! $id ) {
            throw new \RuntimeException( 'Could not create test document' );
        }
        $created[ $name ] = $id;
    }

    wp_set_current_user( 0 );
    $checks['guest_published_form_document_allowed'] =
        true === $utils::is_form_submission_document_accessible( $created['published'] );
    foreach ( [ 'draft', 'private', 'protected', 'trash' ] as $name ) {
        $checks['guest_' . $name . '_form_document_denied'] =
            false === $utils::is_form_submission_document_accessible( $created[ $name ] );
    }
    $checks['guest_missing_document_denied'] =
        false === $utils::is_form_submission_document_accessible( 0 )
        && false === $utils::is_form_submission_document_accessible( 999999999 );
    $checks['guest_non_scalar_document_denied'] =
        false === $utils::is_form_submission_document_accessible( [ $created['published'] ] );

    $controller = new $atomic_class();
    $method = new \ReflectionMethod( $atomic_class, 'find_form_element' );
    foreach ( [ 'draft', 'private', 'protected' ] as $name ) {
        $result = $method->invoke( $controller, $created[ $name ], 'test-form' );
        $checks['atomic_guest_' . $name . '_denied_before_read'] =
            is_wp_error( $result ) && 'form_not_found' === $result->get_error_code();
    }

    wp_set_current_user( $editor_id );
    foreach ( [ 'published', 'draft', 'private', 'protected' ] as $name ) {
        $checks['editor_can_test_own_' . $name . '_document'] =
            true === $utils::is_form_submission_document_accessible( $created[ $name ] );
    }
} finally {
    wp_set_current_user( $old_user );
    foreach ( $created as $id ) {
        wp_delete_post( $id, true );
    }
    // The entire synthetic WordPress database is discarded by the QA
    // harness. Deleting an authored editor here also invokes unrelated
    // Elementor Notes delete_user hooks during WP-CLI teardown, which can
    // fail independently of Form visibility. No persistent user survives.
    // Never execute this fixture against a production database.
}

foreach ( $checks as $name => $ok ) {
    echo ( $ok ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) < 14 || in_array( false, $checks, true ) ) {
    exit( 4 );
}
