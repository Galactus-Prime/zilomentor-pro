<?php
namespace ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets;

use ElementorPro\Core\Utils;

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

class Fontello extends Icon_Set_Base {

	const DEFAULT_NAME = 'fontello';

	protected $data_file = 'config.json';
	protected $stylesheet_file = '';
	protected $allowed_zipped_files = [ 'config.json', 'demo.html', 'README.txt', 'LICENSE.txt', 'css/', 'font/' ];
	protected $allowed_webfont_extensions = [ 'woff', 'woff2', 'ttf', 'svg', 'otf' ];

	protected function prepare() {
		$this->remove_fontello_styling();
		$this->dir_name = $this->get_unique_name();
	}

	public function get_type() {
		return esc_html__( 'Fontello', 'elementor-pro' );
	}

	public function is_valid() {
		if ( ! file_exists( $this->directory . $this->data_file ) ) {
			return false; // missing data file
		}
		return true;
	}

	private function remove_fontello_styling() {
		$filename = $this->directory . 'css/' . $this->get_name() . '.css';
		if ( ! is_file( $filename ) || is_link( $filename ) || ! is_readable( $filename ) ) {
			return;
		}
		$stylesheet = Utils::_unstable_file_get_contents( $filename );
		if ( ! is_string( $stylesheet ) || '' === trim( $stylesheet ) ) {
			return;
		}
		$stylesheet = str_replace( [ 'margin-left: .2em;', 'margin-right: .2em;' ], [ '', '' ], $stylesheet );
		file_put_contents( $filename, $stylesheet );
	}

	private function get_json() {
		return json_decode( Utils::_unstable_file_get_contents( $this->directory . $this->data_file ) );
	}

	protected function extract_icon_list() {
		$config = $this->get_json();
		if ( ! isset( $config->glyphs ) || ! is_array( $config->glyphs ) || count( $config->glyphs ) > 8192 ) {
			return false; //  missing icons list
		}
		$name = $this->get_name();
		if ( false === $name || ! is_file( $this->directory . 'css/' . $name . '.css' ) ) {
			return false;
		}
		$icons = [];
		foreach ( $config->glyphs as $icon ) {
			if ( ! is_object( $icon ) || ! isset( $icon->css ) || ! is_string( $icon->css ) ) {
				return false;
			}
			$icons[] = $icon->css;
		}
		return $icons;
	}

	protected function get_prefix() {
		$config = $this->get_json();
		if ( ! isset( $config->css_prefix_text ) ) {
			return false; //  missing css_prefix_text
		}
		return $config->css_prefix_text;
	}

	public function get_name() {
		$config = $this->get_json();

		if ( ! isset( $config->name ) || ! is_string( $config->name ) ) {
			return false; //  missing name
		}

		$name = $config->name;

		// A default fontello.com export has an empty name and names its css and font files "fontello".
		return '' === trim( $name ) ? self::DEFAULT_NAME : $name;
	}

	/**
	 * Fontello includes alternative embedded/IE7 demo stylesheets and a
	 * legacy external SVG 1.1 DOCTYPE in otherwise usable webfont packs.
	 * Neither is required for the enqueued modern stylesheet. Discard the
	 * alternative CSS and strip only the exact known external declaration
	 * in the private extracted copy; all retained assets still pass the
	 * shared strict validator before anything is published.
	 */
	public function validate_public_icon_assets() {
		$error = new \WP_Error( 'invalid_icon_assets', esc_html__( 'Unable to prepare Fontello assets safely.', 'elementor-pro' ) );
		$name_validation = $this->validate_name();
		if ( is_wp_error( $name_validation ) ) {
			return $name_validation;
		}
		$root = realpath( $this->directory );
		if ( ! $root || is_link( rtrim( $this->directory, '/\\' ) ) ) {
			return $error;
		}
		foreach ( [ 'css', 'font' ] as $folder ) {
			$path = $root . '/' . $folder;
			if ( is_link( $path ) || ! is_dir( $path ) || realpath( $path ) !== $path ) {
				return $error;
			}
		}
		$name = $this->get_name();
		foreach ( [ '-embedded.css', '-ie7.css', '-ie7-codes.css' ] as $suffix ) {
			$file = $root . '/css/' . $name . $suffix;
			if ( is_link( $file ) || ( file_exists( $file ) && ( ! is_file( $file ) || ! unlink( $file ) ) ) ) {
				return $error;
			}
		}
		$svg = $root . '/font/' . $name . '.svg';
		if ( is_link( $svg ) ) {
			return $error;
		}
		if ( is_file( $svg ) ) {
			$size = filesize( $svg );
			if ( false === $size || $size < 1 || $size > 2 * 1024 * 1024 ) {
				return $error;
			}
			$data = file_get_contents( $svg );
			if ( ! is_string( $data ) ) {
				return $error;
			}
			$declaration = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">';
			$pattern = '~\A(\s*(?:<\?xml[^?]*\?>\s*)?)' . preg_quote( $declaration, '~' ) . '(?=\s*<svg\b)~';
			$normalized = preg_replace( $pattern, '$1', $data, 1 );
			if ( ! is_string( $normalized ) || ( $normalized !== $data && strlen( $normalized ) !== file_put_contents( $svg, $normalized ) ) ) {
				return $error;
			}
		}
		return parent::validate_public_icon_assets();
	}

	protected function get_stylesheet() {
		$name = $this->get_name();
		if ( ! $name ) {
			return false; //  missing name
		}
		return $this->get_url() . '/css/' . $name . '.css';
	}
}
