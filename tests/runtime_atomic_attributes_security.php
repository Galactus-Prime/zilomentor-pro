<?php
/**
 * Atomic Attributes HTML injection and URL-protocol regression.
 * CLI-only and explicitly isolated. Never execute against live content.
 */
if ( ! defined( 'ABSPATH' ) || getenv( 'ZMP_ISOLATED_QA' ) !== 'yes' ) {
    exit( 2 );
}
$transformer_class = '\\ElementorPro\\Modules\\Attributes\\PropsResolver\\Transformers\\Settings\\Pro_Attributes_Transformer';
$context_class = '\\Elementor\\Modules\\AtomicWidgets\\PropsResolver\\Props_Resolver_Context';
if ( ! class_exists( $transformer_class ) || ! class_exists( $context_class ) ) {
    fwrite( STDERR, "Atomic Attributes classes not available\n" );
    exit( 3 );
}
$t = new $transformer_class();
$ctx = $context_class::make();
$input = [
    [ 'key' => 'title', 'value' => 'Safe" onclick="alert(1)' ],
    [ 'key' => 'onclick', 'value' => 'alert(1)' ],
    [ 'key' => 'onmouseover', 'value' => 'alert(1)' ],
    [ 'key' => 'srcdoc', 'value' => '<script>alert(1)</script>' ],
    [ 'key' => 'style', 'value' => 'background:url(javascript:alert(1))' ],
    [ 'key' => 'href', 'value' => 'javascript:alert(1)' ],
    [ 'key' => 'href', 'value' => 'https://example.invalid/?a=1&b=2' ],
    [ 'key' => 'DATA-qa', 'value' => 'escaped & useful' ],
    [ 'key' => 'aria-label', 'value' => '<img src=x onerror=alert(1)>' ],
    [ 'key' => 'bad name', 'value' => 'no' ],
    [ 'key' => 'bad"foo', 'value' => 'no' ],
    [ 'key' => 'href', 'value' => 'data:text/html,<script>alert(1)</script>' ],
    [ 'key' => [], 'value' => 'invalid' ],
    [ 'key' => 'role', 'value' => [ 'invalid' ] ],
    null,
];
$output = $t->transform( $input, $ctx );
$checks = [
    'quoted_value_escaped' => false !== strpos( $output, 'title="Safe&quot; onclick=&quot;alert(1)"' ),
    'event_handler_excluded' => false === strpos( $output, ' onclick="' )
        && false === strpos( $output, ' onmouseover="' ),
    'srcdoc_and_style_excluded' => false === strpos( $output, 'srcdoc=' )
        && false === strpos( $output, 'style=' ),
    'unsafe_protocol_excluded' => false === strpos( $output, 'javascript:' )
        && false === strpos( $output, 'data:text/html' ),
    'valid_url_retained' => false !== strpos( $output, 'href="https://example.invalid/' ),
    'data_attr_retained' => false !== strpos( $output, 'data-qa="escaped &amp; useful"' ),
    'aria_attr_escaped' => false !== strpos( $output, 'aria-label="&lt;img' ),
    'invalid_attribute_names_excluded' => false === strpos( $output, 'bad name=' )
        && false === strpos( $output, 'bad"foo=' ),
    'empty_input_is_empty' => '' === $t->transform( [], $ctx ),
    'non_array_is_null' => null === $t->transform( 'unsafe', $ctx ),
];
foreach ( $checks as $name => $passed ) {
    echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( in_array( false, $checks, true ) ) {
    exit( 4 );
}
