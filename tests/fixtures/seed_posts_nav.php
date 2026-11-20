<?php
/**
 * Synthetic Posts and WordPress Menu widget fixtures on disposable WordPress.
 * Never create a navigation menu, post or Elementor page in production.
 */
if ( ! defined( 'ABSPATH' ) || getenv( 'ZMP_ISOLATED_QA' ) !== 'yes'
    || ! class_exists( '\ElementorPro\Modules\Posts\Widgets\Posts' )
    || ! class_exists( '\ElementorPro\Modules\NavMenu\Widgets\Nav_Menu' ) ) {
    exit( 2 );
}
$label = 'ZiloMentor QA Navigation Destination';
$post_marker = 'ZiloMentor QA Posts Listing Item';
$post_id = wp_insert_post( [
    'post_type' => 'post',
    'post_status' => 'publish',
    'post_title' => $post_marker,
    'post_content' => 'Synthetic Posts widget item, created only in disposable WordPress',
], true );
$destination_id = wp_insert_post( [
    'post_type' => 'page',
    'post_status' => 'publish',
    'post_title' => $label,
    'post_content' => 'Synthetic only page for a test navigation link',
], true );
$menu = wp_create_nav_menu( 'zmp-synthetic-nav' );
if ( is_wp_error( $post_id ) || is_wp_error( $destination_id )
    || is_wp_error( $menu ) ) {
    fwrite( STDERR, "Cannot create disposable Posts and Menu fixtures\n" );
    exit( 3 );
}
$link = wp_update_nav_menu_item( $menu, 0, [
    'menu-item-title' => $label,
    'menu-item-type' => 'post_type',
    'menu-item-object' => 'page',
    'menu-item-object-id' => (int) $destination_id,
    'menu-item-status' => 'publish',
] );
if ( is_wp_error( $link ) || ! $link ) {
    fwrite( STDERR, "Cannot create synthetic menu item\n" );
    exit( 3 );
}
$test_page = wp_insert_post( [
    'post_type' => 'page',
    'post_status' => 'publish',
    'post_title' => 'ZMP Synthetic Posts And Navigation',
], true );
if ( is_wp_error( $test_page ) || ! $test_page ) {
    fwrite( STDERR, "Cannot create isolated widget page\n" );
    exit( 3 );
}
$elements = [ [
    'id' => '9a0c1d00',
    'elType' => 'container',
    'settings' => [],
    'elements' => [
        [
            'id' => '9a0c1d01',
            'elType' => 'widget',
            'widgetType' => 'nav-menu',
            'settings' => [
                'menu' => 'zmp-synthetic-nav',
                'menu_name' => 'ZMP Synthetic Menu',
                'layout' => 'horizontal',
            ],
            'elements' => [],
        ],
        [
            'id' => '9a0c1d02',
            'elType' => 'widget',
            'widgetType' => 'posts',
            'settings' => [
                'posts_post_type' => 'post',
                'posts_per_page' => 4,
            ],
            'elements' => [],
        ],
    ],
    'isInner' => false,
] ];
update_post_meta( $test_page, '_elementor_data', wp_slash( wp_json_encode( $elements ) ) );
update_post_meta( $test_page, '_elementor_edit_mode', 'builder' );
update_post_meta( $test_page, '_elementor_version', ELEMENTOR_VERSION );

echo wp_json_encode( [
    'page' => (int) $test_page,
    'menu' => (int) $menu,
    'menu_label' => $label,
    'posts_label' => $post_marker,
    'nav_id' => '9a0c1d01',
    'posts_id' => '9a0c1d02',
] );
