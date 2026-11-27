<?php
namespace ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets;

use ElementorPro\Core\Utils;

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

class Fontastic extends Icon_Set_Base {

	protected $data = '';
	protected $cached_icon_prefix = null;
	protected $cached_icon_name = null;
	protected $data_file = 'icons-reference.html';
	protected $stylesheet_file = 'styles.css';
	protected $allowed_zipped_files = [ 'icons-reference.html', 'styles.css', 'fonts/' ];
	protected $allowed_webfont_extensions = [ 'woff', 'ttf', 'svg', 'eot' ];

	protected function prepare() {
		$this->data = Utils::_unstable_file_get_contents( $this->directory . $this->stylesheet_file );
		$this->dir_name = $this->get_unique_name();
	}

	public function get_type() {
		return esc_html__( 'Fontastic', 'elementor-pro' );
	}

	public function is_valid() {
		if ( ! file_exists( $this->directory . $this->data_file ) ) {
			return false; // missing data file
		}
		return true;
	}

	protected function extract_icon_list() {
		$prefix = $this->get_prefix();
		if ( ! is_string( $prefix ) || '' === $prefix ) {
			return false;
		}
		$pattern = '/\.' . preg_quote( $prefix, '/' ) . '([a-zA-Z0-9_-]+):before\s*\{/';
		preg_match_all( $pattern, $this->data, $icons_matches );
		if ( empty( $icons_matches[1] ) ) {
			return false; //  missing icons list
		}
		$icons = [];
		foreach ( $icons_matches[1] as $icon ) {
			$icons[] = $icon;
		}
		return $icons;
	}

	protected function get_prefix() {
		if ( null === $this->cached_icon_prefix ) {
			$pattern = '/class\^="([^"]+)"/';
			preg_match_all( $pattern, $this->data, $prefix );
			if ( ! isset( $prefix[1][0] ) ) {
				return false; //  missing css_prefix_text
			}
			$this->cached_icon_prefix = $prefix[1][0];
		}
		return $this->cached_icon_prefix;
	}

	const DEFAULT_NAME = 'fontastic';

	public function get_name() {
		if ( null === $this->cached_icon_name ) {
			// The name is validated before prepare() loads the stylesheet.
			if ( '' === $this->data ) {
				$this->data = Utils::_unstable_file_get_contents( $this->directory . $this->stylesheet_file );
			}

			$pattern = '/font-family:\s*"([^"]+)"/';
			preg_match_all( $pattern, $this->data, $name );
			if ( ! isset( $name[1][0] ) ) {
				return false; //  missing name
			}
			$this->cached_icon_name = '' === trim( $name[1][0] ) ? self::DEFAULT_NAME : $name[1][0];
		}
		return $this->cached_icon_name;
	}

	protected function get_stylesheet( $unique_name = '' ) {
		return $this->get_url() . '/' . $this->stylesheet_file;
	}
}
