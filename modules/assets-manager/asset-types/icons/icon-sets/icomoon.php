<?php
namespace ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets;

use ElementorPro\Core\Utils;

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

class Icomoon extends Icon_Set_Base {

	const DEFAULT_NAME = 'icomoon';

	private $modern_project_file = null;
	private $modern_project = null;
	private $modern_root = null;

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
			return false !== $this->get_modern_project_file(); // modern project export
		}
		return true;
	}

	private function get_json() {
		return json_decode( Utils::_unstable_file_get_contents( $this->directory . $this->data_file ) );
	}

	protected function extract_icon_list() {
		if ( false !== $this->get_modern_project_file() ) {
			$glyphs = $this->get_modern_glyphs();
			return is_array( $glyphs ) ? array_keys( $glyphs ) : false;
		}
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
		if ( false !== $this->get_modern_project_file() ) {
			return 'zmp-' . $this->get_name() . '-';
		}
		$config = $this->get_json();
		if ( ! isset( $config->preferences->fontPref->prefix ) ) {
			return false; //  missing css_prefix_text
		}
		return $config->preferences->fontPref->prefix;
	}

	protected function get_display_prefix() {
		if ( false !== $this->get_modern_project_file() ) {
			return '';
		}
		$config = $this->get_json();
		if ( ! isset( $config->preferences->fontPref->classSelector ) || ! is_string( $config->preferences->fontPref->classSelector ) ) {
			return false; //  missing css_prefix_text
		}
		return str_replace( '.', '', $config->preferences->fontPref->classSelector );
	}

	public function get_name() {
		$modern_file = $this->get_modern_project_file();
		if ( false !== $modern_file ) {
			return substr( basename( $modern_file ), 0, -strlen( '.icomoon.json' ) );
		}
		$config = $this->get_json();
		if ( ! isset( $config->metadata->name ) || ! is_string( $config->metadata->name ) ) {
			return false; //  missing name
		}
		$name = $config->metadata->name;
		// A default icomoon.io export has an empty name and names its font files "icomoon".
		return '' === trim( $name ) ? self::DEFAULT_NAME : $name;
	}

	/**
	 * Modern IcoMoon beta exports a project JSON and separate font/SVG
	 * folders. Only a single unambiguous, named font project is accepted.
	 * The original SVG/demo assets are not published.
	 */
	private function get_modern_project_file() {
		if ( null !== $this->modern_project_file ) {
			return $this->modern_project_file;
		}
		$this->modern_project_file = false;
		if ( file_exists( $this->directory . $this->data_file ) ) {
			return false;
		}
		$files = glob( $this->directory . '*.icomoon.json' );
		if ( ! is_array( $files ) || 1 !== count( $files ) ) {
			return false;
		}
		$file = $files[0];
		if ( ! preg_match( '~^[A-Za-z][A-Za-z0-9_-]{0,79}\.icomoon\.json$~D', basename( $file ) )
			|| is_link( $file ) || ! is_file( $file ) || filesize( $file ) > 8 * 1024 * 1024 ) {
			return false;
		}
		$this->modern_project_file = $file;
		return $file;
	}

	private function get_modern_glyphs() {
		$file = $this->get_modern_project_file();
		if ( false === $file ) {
			return false;
		}
		if ( null === $this->modern_project ) {
			$data = Utils::_unstable_file_get_contents( $file );
			$this->modern_project = is_string( $data ) ? json_decode( $data ) : false;
		}
		$config = $this->modern_project;
		if ( ! isset( $config->formats, $config->glyphs ) || ! is_array( $config->formats )
			|| ! is_array( $config->glyphs ) || ! $config->glyphs || count( $config->glyphs ) > 8192 ) {
			return false;
		}
		$font_format = false;
		foreach ( $config->formats as $format ) {
			if ( isset( $format->item->tag ) && 'ItemFont' === $format->item->tag ) {
				$font_format = true;
			}
		}
		if ( ! $font_format ) {
			return false;
		}
		$glyphs = [];
		foreach ( $config->glyphs as $glyph ) {
			$name = $glyph->extras->name ?? null;
			$point = $glyph->extras->codePoint ?? null;
			if ( ! is_string( $name ) || ! preg_match( '~^[A-Za-z][A-Za-z0-9_-]{0,127}$~D', $name )
				|| isset( $glyphs[ $name ] ) || ! is_int( $point ) || $point < 33 || $point > 0x10ffff
				|| ( $point >= 0xd800 && $point <= 0xdfff ) ) {
				return false;
			}
			$glyphs[ $name ] = $point;
		}
		return $glyphs;
	}

	public function validate_public_icon_assets() {
		if ( false === $this->get_modern_project_file() ) {
			return parent::validate_public_icon_assets();
		}
		$error = new \WP_Error( 'invalid_icon_assets', esc_html__( 'Invalid modern IcoMoon font export.', 'elementor-pro' ) );
		$glyphs = $this->get_modern_glyphs();
		$root = realpath( $this->directory );
		if ( ! $glyphs || ! $root || is_link( rtrim( $this->directory, '/\\' ) ) ) {
			return $error;
		}
		$font_root = $root . '/font';
		$fonts = $font_root . '/fonts';
		$style = $font_root . '/style.css';
		if ( realpath( $font_root ) !== $font_root || realpath( $fonts ) !== $fonts
			|| is_link( $font_root ) || is_link( $fonts ) || is_link( $style ) || ! is_file( $style ) ) {
			return $error;
		}
		// Regenerate a minimal glyph stylesheet from validated metadata and
		// actual fonts. The new generator may omit WOFF2 yet reference it.
		// Never publish arbitrary original project CSS or its SVG exports.
		$extensions = [
			'woff2' => [ 'wOF2', 'woff2' ],
			'woff' => [ 'wOFF', 'woff' ],
			'ttf' => [ "\x00\x01\x00\x00", 'truetype' ],
			'otf' => [ 'OTTO', 'opentype' ],
		];
		$available = [];
		$stem = null;
		foreach ( scandir( $fonts ) as $entry ) {
			if ( '.' === $entry || '..' === $entry ) {
				continue;
			}
			$path = $fonts . '/' . $entry;
			$ext = strtolower( pathinfo( $entry, PATHINFO_EXTENSION ) );
			$current_stem = pathinfo( $entry, PATHINFO_FILENAME );
			if ( ! isset( $extensions[ $ext ] ) || isset( $available[ $ext ] )
				|| ! preg_match( '~^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$~D', $current_stem )
				|| ( null !== $stem && $stem !== $current_stem ) || is_link( $path ) || ! is_file( $path )
				|| filesize( $path ) < 12 || $extensions[ $ext ][0] !== file_get_contents( $path, false, null, 0, 4 ) ) {
				return $error;
			}
			$stem = $current_stem;
			$available[ $ext ] = $entry;
		}
		if ( ! $available ) {
			return $error;
		}
		$src = [];
		foreach ( $extensions as $ext => $format ) {
			if ( isset( $available[ $ext ] ) ) {
				$src[] = 'url("fonts/' . $available[ $ext ] . '") format("' . $format[1] . '")';
			}
		}
		$family = 'zmp-' . $this->get_name();
		$prefix = $this->get_prefix();
		$css = '@font-face{font-family:"' . $family . '";src:' . implode( ',', $src )
			. ';font-weight:normal;font-style:normal;font-display:block;}' . "\n"
			. '[class^="' . $prefix . '"],[class*=" ' . $prefix . '"]{font-family:"'
			. $family . '" !important;font-style:normal;font-weight:normal;line-height:1;}' . "\n";
		foreach ( $glyphs as $name => $point ) {
			$css .= '.' . $prefix . $name . ':before{content:"\\' . dechex( $point ) . '";}' . "\n";
		}
		if ( strlen( $css ) !== file_put_contents( $style, $css ) ) {
			return $error;
		}
		// Scope publication to the font subtree. Keep any conventional text
		// licensing notices from the root, without copying project metadata.
		foreach ( scandir( $root ) as $entry ) {
			if ( ! preg_match( '~^(?:licen[cs]e|readme)(?:[-_.][A-Za-z0-9_.-]+)?\.txt$~iD', $entry ) ) {
				continue;
			}
			$source = $root . '/' . $entry;
			$target = $font_root . '/' . $entry;
			if ( is_link( $source ) || is_link( $target ) || ! is_file( $source )
				|| ( ! file_exists( $target ) && ! copy( $source, $target ) ) ) {
				return $error;
			}
		}
		$this->modern_root = $root;
		$this->directory = trailingslashit( $font_root );
		return parent::validate_public_icon_assets();
	}

	protected function cleanup_temp_files( $wp_filesystem ) {
		if ( $this->modern_root && dirname( rtrim( $this->directory, '/' ) ) === $this->modern_root ) {
			$wp_filesystem->rmdir( $this->modern_root, true );
			return;
		}
		parent::cleanup_temp_files( $wp_filesystem );
	}

	protected function get_stylesheet() {
		return $this->get_url( '/' . $this->stylesheet_file );
	}
}
