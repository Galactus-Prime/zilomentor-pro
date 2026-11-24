<?php
namespace ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets;

use ElementorPro\Core\Utils;

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

class Icomoon extends Icon_Set_Base {

	const DEFAULT_NAME = 'icomoon';

	protected $data_file = 'selection.json';
	protected $stylesheet_file = 'style.css';
	protected $allowed_zipped_files = [ 'selection.json', 'demo.html', 'Read Mw.txt', 'demo-files/', 'fonts/' ];
	protected $allowed_webfont_extensions = [ 'woff', 'ttf', 'svg', 'eot' ];

	protected function prepare() {
		$this->dir_name = $this->get_unique_name();
		return [];
	}

	public function get_type() {
		return esc_html__( 'Icomoon', 'elementor-pro' );
	}

	public function is_valid() {
		if ( ! file_exists( $this->directory . $this->data_file ) ) {
			return false; // missing data file
		}
		return true;
	}

	private function get_json() {
		return json_decode( Utils::_unstable_file_get_contents( $this->directory . $this->data_file ) );
	}

	protected function extract_icon_list() {
		$config = $this->get_json();
		if ( ! isset( $config->icons ) || ! is_array( $config->icons ) || count( $config->icons ) > 8192 || ! is_file( $this->directory . $this->stylesheet_file ) ) {
			return false; //  missing icons list
		}
		$icons = [];
		foreach ( $config->icons as $icon ) {
			if ( ! is_object( $icon ) || ! isset( $icon->properties->name ) || ! is_string( $icon->properties->name ) ) {
				return false;
			}
			$icons[] = $icon->properties->name;
		}
		return $icons;
	}

	protected function get_prefix() {
		$config = $this->get_json();
		if ( ! isset( $config->preferences->fontPref->prefix ) ) {
			return false; //  missing css_prefix_text
		}
		return $config->preferences->fontPref->prefix;
	}

	protected function get_display_prefix() {
		$config = $this->get_json();
		if ( ! isset( $config->preferences->fontPref->classSelector ) || ! is_string( $config->preferences->fontPref->classSelector ) ) {
			return false; //  missing css_prefix_text
		}
		return str_replace( '.', '', $config->preferences->fontPref->classSelector );
	}

	public function get_name() {
		$config = $this->get_json();
		if ( ! isset( $config->metadata->name ) || ! is_string( $config->metadata->name ) ) {
			return false; //  missing name
		}
		$name = $config->metadata->name;
		// A default icomoon.io export has an empty name and names its font files "icomoon".
		return '' === trim( $name ) ? self::DEFAULT_NAME : $name;
	}

	protected function get_stylesheet() {
		return $this->get_url( '/' . $this->stylesheet_file );
	}
}
