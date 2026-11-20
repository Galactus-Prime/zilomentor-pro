<?php
/**
 * Stripe security regression; no real provider keys, network calls,
 * actual purchases, or production data. Disposable WordPress only.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
    exit( 2 );
}

$class = '\\ElementorPro\\Modules\\Payments\\Module';
if ( ! class_exists( $class ) ) {
    fwrite( STDERR, "Stripe payment module unavailable\n" );
    exit( 3 );
}
$tests = [];
$object = ( new \ReflectionClass( $class ) )->newInstanceWithoutConstructor();

$allowed = home_url( '/synthetic-payment-return/' );
$tests['local_https_return_url_retained'] =
    $allowed === $class::validate_checkout_return_url( $allowed, home_url( '/' ) );
$tests['external_return_url_rejected'] =
    home_url( '/' ) === $class::validate_checkout_return_url(
        'https://malicious.example.invalid/collect-card', home_url( '/' )
    );
$tests['javascript_return_url_rejected'] =
    home_url( '/' ) === $class::validate_checkout_return_url(
        'javascript:alert(1)', home_url( '/' )
    );
$tests['protocol_relative_return_url_rejected'] =
    home_url( '/' ) === $class::validate_checkout_return_url(
        '//malicious.example.invalid/', home_url( '/' )
    );
$tests['non_string_return_url_rejected'] =
    home_url( '/' ) === $class::validate_checkout_return_url(
        [ 'invalid array' ], home_url( '/' )
    );
$tests['empty_return_url_safe_fallback'] =
    home_url( '/' ) === $class::validate_checkout_return_url( '', home_url( '/' ) );

$pub = wp_insert_post( [
    'post_title' => 'ZiloMentor QA published Stripe page',
    'post_type' => 'page',
    'post_status' => 'publish',
], true );
$draft = wp_insert_post( [
    'post_title' => 'ZiloMentor QA unpublished Stripe page',
    'post_type' => 'page',
    'post_status' => 'draft',
], true );
$locked = wp_insert_post( [
    'post_title' => 'ZiloMentor QA password-protected Stripe page',
    'post_type' => 'page',
    'post_status' => 'publish',
    'post_password' => wp_generate_password( 18, false ),
], true );
if ( is_wp_error( $pub ) || is_wp_error( $draft ) || is_wp_error( $locked ) ) {
    fwrite( STDERR, "Cannot create isolated Stripe post status fixtures\n" );
    exit( 3 );
}
try {
    $tests['published_stripe_document_allowed'] = $class::is_public_stripe_document( $pub );
    $tests['draft_stripe_document_denied'] = ! $class::is_public_stripe_document( $draft );
    $tests['password_protected_document_denied'] = ! $class::is_public_stripe_document( $locked );
    $tests['missing_document_denied'] = ! $class::is_public_stripe_document( PHP_INT_MAX );
    $tests['invalid_document_id_denied'] = ! $class::is_public_stripe_document( 0 );

    $tests['usd_cents_calculated'] = 125 === $object->currency_adaptation( 'USD', '1.25' );
    $tests['fractional_cents_19_99_not_undercharged'] = 1999 === $object->currency_adaptation( 'GBP', '19.99' );
    $tests['fractional_cents_10_29_not_undercharged'] = 1029 === $object->currency_adaptation( 'USD', '10.29' );
    $tests['jpy_zero_decimal_amount'] = 555 === $object->currency_adaptation( 'JPY', '555.55' );
    $tests['invalid_price_rejected'] = 0 === $object->currency_adaptation( 'USD', '<?php 2' );
    $tests['negative_price_rejected'] = 0 === $object->currency_adaptation( 'USD', -12 );
    $tests['infinite_price_rejected'] = 0 === $object->currency_adaptation( 'USD', INF );

    $good = [ 'currency' => 'GBP', 'quantity' => 2, 'unit_amount' => 1299 ];
    $tests['valid_payment_settings_allowed'] = $class::is_valid_stripe_session( $good );
    $tests['zero_price_rejected'] = ! $class::is_valid_stripe_session( array_merge( $good, [ 'unit_amount' => 0 ] ) );
    $tests['negative_price_session_rejected'] = ! $class::is_valid_stripe_session( array_merge( $good, [ 'unit_amount' => -1 ] ) );
    $tests['oversized_price_rejected'] = ! $class::is_valid_stripe_session( array_merge( $good, [ 'unit_amount' => 100000000 ] ) );
    $tests['oversized_total_rejected'] = ! $class::is_valid_stripe_session(
        array_merge( $good, [ 'unit_amount' => 99999999, 'quantity' => 2 ] )
    );
    $tests['zero_quantity_rejected'] = ! $class::is_valid_stripe_session( array_merge( $good, [ 'quantity' => 0 ] ) );
    $tests['oversized_quantity_rejected'] = ! $class::is_valid_stripe_session( array_merge( $good, [ 'quantity' => 100 ] ) );
    $tests['invalid_currency_rejected'] = ! $class::is_valid_stripe_session( array_merge( $good, [ 'currency' => 'GBP<script>' ] ) );

    $params = [
        'page_url' => $allowed,
        'success_url' => $allowed,
        'currency' => 'GBP',
        'quantity' => 2,
        'unit_amount' => 1299,
        'product_name' => 'Synthetic demo',
        'shipping_amount' => 0,
        'tax_rates' => '',
    ];
    $warnings = [];
    $handler = static function ( $errno, $message ) use ( &$warnings ) {
        $warnings[] = (string) $message;
        return true;
    };
    set_error_handler( $handler );
    try {
        $none = $object->build_body_for_post_request( $params );
        $params['tax_rates'] = '{broken';
        $corrupt = $object->build_body_for_post_request( $params );
        $params['tax_rates'] = '["txr_SAFE123","exclusive"]';
        $valid_tax = $object->build_body_for_post_request( $params );
        $params['tax_rates'] = '["bad<script>","inclusive"]';
        $invalid_tax = $object->build_body_for_post_request( $params );
    } finally {
        restore_error_handler();
    }
    $tests['missing_tax_does_not_warn'] = 0 === count( $warnings );
    $tests['invalid_tax_does_not_insert_tax'] = ! isset( $corrupt['line_items'] )
        && ! isset( $invalid_tax['line_items'] );
    $tests['valid_tax_retains_expected_id_and_behavior'] =
        ( $valid_tax['line_items'][0]['tax_rates'][0] ?? null ) === 'txr_SAFE123'
        && ( $valid_tax['line_items'][0]['price_data']['tax_behavior'] ?? null ) === 'exclusive';
    $tests['checkout_total_from_saved_settings'] = 1299 ===
        $none['line_items[0][price_data][unit_amount]']
        && 2 === $none['line_items[0][quantity]'];
} finally {
    wp_delete_post( $pub, true );
    wp_delete_post( $draft, true );
    wp_delete_post( $locked, true );
}

foreach ( $tests as $name => $ok ) {
    echo ( $ok ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( in_array( false, $tests, true ) || count( $tests ) < 20 ) {
    exit( 4 );
}
