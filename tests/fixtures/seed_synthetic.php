<?php
/**
 * Seed ONLY a disposable WordPress database with synthetic QA fixtures.
 *
 * This file intentionally rejects normal execution unless its test-specific
 * environment flag is present, so it must never be run on a live website.
 * Called from: tools/qa_isolated_site.py
 */
if ( ! defined( 'ABSPATH' ) || getenv( 'ZMP_ISOLATED_QA' ) !== 'yes' ) {
    exit( 2 );
}
if ( ! class_exists( 'WC_Product_Simple' ) || ! did_action( 'elementor/loaded' ) ) {
    fwrite( STDERR, "Missing Elementor or WooCommerce runtime\n" );
    exit( 3 );
}
$page_id = wp_insert_post( [
    'post_type' => 'page',
    'post_status' => 'publish',
    'post_title' => 'ZiloMentor Synthetic Elementor Page',
] );
$form_id = '1a2b3c4d';
$elements = [
    [
        'id' => '1a2b3c00',
        'elType' => 'container',
        'settings' => [],
        'elements' => [
            [
                'id' => '1a2b3c01',
                'elType' => 'widget',
                'widgetType' => 'heading',
                'settings' => [ 'title' => 'ZiloMentor Synthetic Heading' ],
                'elements' => [],
            ],
            [
                'id' => '1a2b3c02',
                'elType' => 'widget',
                'widgetType' => 'heading',
                'settings' => [
                    'title' => 'ACF Dynamic Fallback',
                    '__dynamic__' => [
                        'title' => \Elementor\Plugin::instance()->dynamic_tags->tag_data_to_tag_text(
                            'zmp-qa-acf-heading', 'acf-text',
                            [ 'key' => 'field_zmp_qa_text:zmp_qa_text' ]
                        ),
                    ],
                ],
                'elements' => [],
            ],
            [
                'id' => $form_id,
                'elType' => 'widget',
                'widgetType' => 'form',
                'settings' => [
                    'form_name' => 'ZiloMentor Synthetic Form',
                    'form_fields' => [
                        [
                            'custom_id' => 'email',
                            'field_type' => 'email',
                            'field_label' => 'Email',
                            'required' => 'true',
                        ],
                    ],
                    'submit_actions' => [],
                    'button_text' => 'Submit',
                ],
                'elements' => [],
            ],
        ],
        'isInner' => false,
    ],
];
update_post_meta( $page_id, '_elementor_data', wp_slash( wp_json_encode( $elements ) ) );
update_post_meta( $page_id, '_elementor_edit_mode', 'builder' );
update_post_meta( $page_id, '_elementor_version', ELEMENTOR_VERSION );
if ( function_exists( 'update_field' ) ) {
    update_field( 'field_zmp_qa_text', 'ZiloMentor Synthetic ACF Value', $page_id );
}
$product = new WC_Product_Simple();
$product->set_name( 'ZiloMentor Synthetic Test Product' );
$product->set_status( 'publish' );
$product->set_regular_price( '9.99' );
$product->set_catalog_visibility( 'visible' );
$product_id = $product->save();

$cart_id = wp_insert_post( [
    'post_type' => 'page',
    'post_status' => 'publish',
    'post_title' => 'ZiloMentor Synthetic Cart',
    'post_content' => '[woocommerce_cart]',
] );
$checkout_id = wp_insert_post( [
    'post_type' => 'page',
    'post_status' => 'publish',
    'post_title' => 'ZiloMentor Synthetic Checkout',
    'post_content' => '[woocommerce_checkout]',
] );
update_option( 'woocommerce_cart_page_id', $cart_id );
update_option( 'woocommerce_checkout_page_id', $checkout_id );

echo wp_json_encode( [
    'page' => $page_id,
    'form' => $form_id,
    'product' => $product_id,
    'product_url' => get_permalink( $product_id ),
    'cart' => $cart_id,
    'checkout' => $checkout_id,
] );
