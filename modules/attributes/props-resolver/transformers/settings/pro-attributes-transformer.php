<?php

namespace ElementorPro\Modules\Attributes\PropsResolver\Transformers\Settings;

use Elementor\Modules\AtomicWidgets\PropsResolver\Props_Resolver_Context;
use Elementor\Modules\AtomicWidgets\PropsResolver\Transformer_Base;

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

class Pro_Attributes_Transformer extends Transformer_Base {
	public function transform( $value, Props_Resolver_Context $context ) {
		if ( ! is_array( $value ) ) {
			return null;
		}

		$attributes = [];

		foreach ( $value as $item ) {
			if ( ! $this->is_valid_attribute_item( $item ) ) {
				continue;
			}

			$key = strtolower( trim( $item['key'] ) );
			$raw = $item['value'];

			// A dynamic attribute name must never introduce new HTML syntax.
			// Event handlers, srcdoc and inline style are deliberately excluded:
			// they require separate, context-specific security validation.
			if ( ! preg_match( '/^[a-z][a-z0-9_:-]*$/D', $key )
				|| str_starts_with( $key, 'on' )
				|| in_array( $key, [ 'srcdoc', 'style' ], true ) ) {
				continue;
			}

			// WordPress maintains the canonical list of attributes that carry
			// URLs. Reject dangerous schemes rather than escaping only quotes.
			if ( in_array( $key, wp_kses_uri_attributes(), true ) ) {
				$raw = esc_url( $raw );
				if ( '' === $raw ) {
					continue;
				}
			} elseif ( preg_match( '/^\\s*(?:javascript|vbscript|data)\\s*:/i', $raw ) ) {
				continue;
			}

			$attributes[] = $key . '="' . esc_attr( $raw ) . '"';
		}

		return implode( ' ', $attributes );
	}

	private function is_valid_attribute_item( $item ): bool {
		return is_array( $item )
			&& isset( $item['key'], $item['value'] )
			&& is_string( $item['key'] )
			&& is_string( $item['value'] )
			&& '' !== trim( $item['key'] )
			&& '' !== $item['value'];
	}
}
