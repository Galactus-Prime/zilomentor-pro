<?php
/**
 * Disposable-only Elementor Theme Builder Header and Popup fixtures.
 * Executed via wp eval-file, never against real or imported WordPress data.
 */
if ( ! defined( 'ABSPATH' ) || getenv( 'ZMP_ISOLATED_QA' ) !== 'yes'
    || ! class_exists( '\ElementorPro\Modules\ThemeBuilder\Module' )
    || ! class_exists( '\ElementorPro\Modules\Popup\Document' ) ) {
    exit( 2 );
}

$target_id = wp_insert_post( [
    'post_type' => 'page',
    'post_status' => 'publish',
    'post_title' => 'ZiloMentor QA Theme Target',
    'post_content' => 'ZiloMentor Theme Target Body',
] );
if ( is_wp_error( $target_id ) || ! $target_id ) {
    fwrite( STDERR, "Unable to seed isolated theme target\n" );
    exit( 3 );
}

$theme = \ElementorPro\Modules\ThemeBuilder\Module::instance();
$types = \Elementor\Plugin::instance()->documents->get_document_types();
$fixtures = [
    'target' => (int) $target_id,
    'documents' => [],
    'conditions_saved' => [],
    'types_registered' => [
        'header' => isset( $types['header'] ),
        'popup' => isset( $types['popup'] ),
    ],
];

foreach ( [
    'header' => [ 'marker' => 'ZMP Synthetic Conditional Header', 'element_id' => '7a0b1c01' ],
    'popup'  => [ 'marker' => 'ZMP Synthetic Conditional Popup',  'element_id' => '7a0b1c02' ],
] as $type => $spec ) {
    if ( empty( $fixtures['types_registered'][ $type ] ) ) {
        continue;
    }
    $template_id = wp_insert_post( [
        'post_type' => 'elementor_library',
        'post_status' => 'publish',
        'post_title' => 'ZMP Synthetic ' . ucfirst( $type ),
    ] );
    if ( is_wp_error( $template_id ) || ! $template_id ) {
        continue;
    }
    update_post_meta( $template_id, '_elementor_template_type', $type );
    update_post_meta( $template_id, '_elementor_edit_mode', 'builder' );
    update_post_meta( $template_id, '_elementor_version', ELEMENTOR_VERSION );
    update_post_meta( $template_id, '_elementor_data', wp_slash( wp_json_encode( [
        [
            'id' => '7a0b1c00',
            'elType' => 'container',
            'settings' => [],
            'elements' => [
                [
                    'id' => $spec['element_id'],
                    'elType' => 'widget',
                    'widgetType' => 'heading',
                    'settings' => [ 'title' => $spec['marker'] ],
                    'elements' => [],
                ],
            ],
            'isInner' => false,
        ],
    ] ) ) );
    if ( 'popup' === $type ) {
        update_post_meta( $template_id, '_elementor_popup_display_settings', [
            // Actual Elementor Popup trigger control keys: page_load=yes
            // and a zero-second page_load_delay.
            'triggers' => [ 'page_load' => 'yes', 'page_load_delay' => 0 ],
            'timing' => [],
        ] );
    }
    $document = $theme->get_document( $template_id );
    $fixtures['documents'][ $type ] = [
        'id' => (int) $template_id,
        'document' => (bool) $document,
        'location' => $document ? $document->get_location() : null,
    ];
    if ( $document ) {
        $saved = $theme->get_conditions_manager()->save_conditions(
            $template_id,
            [ [
                'type' => 'include',
                'name' => 'singular',
                'sub_name' => 'page',
                'sub_id' => (string) $target_id,
            ] ]
        );
        $fixtures['conditions_saved'][ $type ] = (bool) $saved;
    }
}
echo wp_json_encode( $fixtures );
