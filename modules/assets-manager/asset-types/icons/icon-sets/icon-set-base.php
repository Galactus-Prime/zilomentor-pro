<?php
namespace ElementorPro\Modules\AssetsManager\AssetTypes\Icons\IconSets;

use ElementorPro\Core\Utils;
use ElementorPro\Modules\AssetsManager\AssetTypes\Icons\Custom_Icons;

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

abstract class Icon_Set_Base {

	const RESERVED_NAME_PREFIX = 'fa-';

	protected $dir_name = '';
	protected $directory = '';
	protected $data_file = '';
	protected $stylesheet_file = '';
	protected $allowed_zipped_files = [];
	protected $files_to_save = [];
	/**
	 * Webfont extensions.
	 *
	 * @var array
	 */
	protected $allowed_webfont_extensions = [ 'woff', 'woff2', 'ttf', 'svg', 'otf', 'eot' ];

	abstract protected function extract_icon_list();

	abstract protected function prepare();

	abstract protected function get_type();

	abstract public function get_name();

	private function is_path_dir( $path ) {
		return '/' === substr( $path, -1 );
	}

	private function is_file_allowed( $path_name ) {
		$check = $this->directory . $path_name;
		if ( ! file_exists( $check ) ) {
			return false;
		}
		if ( $this->is_path_dir( $path_name ) ) {
			return is_dir( $check );
		}
		return true;
	}

	/**
	 * is icon set
	 *
	 * validate that the current uploaded zip is in this icon set format
	 * @return bool
	 */
	public function is_icon_set() {
		foreach ( $this->allowed_zipped_files as $file ) {
			if ( ! $this->is_file_allowed( $file ) ) {
				return false;
			}
		}
		return true;
	}

	public function is_valid() {
		return false;
	}

	protected function get_display_prefix() {
		return '';
	}

	protected function get_prefix() {
		return '';
	}

	public function handle_new_icon_set() {
		return $this->prepare();
	}

	/**
	 * cleanup_temp_files
	 * @param \WP_Filesystem_Base $wp_filesystem
	 */
	protected function cleanup_temp_files( $wp_filesystem ) {
		$wp_filesystem->rmdir( $this->directory, true );
	}

	/**
	 * Gets the URL to uploaded file.
	 *
	 * @param $file_name
	 *
	 * @return string
	 */
	protected function get_file_url( $file_name ) {
		$wp_upload_dir = wp_upload_dir();
		$url = $wp_upload_dir['baseurl'] . '/elementor/custom-icons/' . $file_name;

		/**
		 * Upload file URL.
		 *
		 * Filters the URL to a file uploaded using custom icons.
		 *
		 * By default URL to a file uploaded is set to `/elementor/custom-icons/{file_name}`
		 * inside the WordPress uploads folder. This hook allows developers to change this URL.
		 *
		 * @since 1.0.0
		 *
		 * @param string $url       File URL.
		 * @param string $file_name File name.
		 */
		$url = apply_filters( 'elementor_pro/icons_manager/custom_icons/url', $url, $file_name );

		return $url;
	}

	protected function get_icon_sets_dir() {
		$wp_upload_dir = wp_upload_dir();
		$path = $wp_upload_dir['basedir'] . '/elementor/custom-icons';

		/**
		 * Upload file path.
		 *
		 * Filters the path to a folder uploaded using custom icons.
		 *
		 * By default the folder path to custom icon files is set to `/elementor/custom-icons`
		 * inside the WordPress uploads folder. This hook allows developers to change this path.
		 *
		 * @param string $path Path to custom icons uploads directory.
		 */
		$path = apply_filters( 'elementor_pro/icons_manager/custom_icons/dir', $path );

		Utils::get_ensure_upload_dir( $path );
		return $path;
	}

	protected function get_ensure_upload_dir( $dir = '' ) {
		$path = $this->get_icon_sets_dir();
		if ( ! empty( $dir ) ) {
			$path .= '/' . $dir;
		}
		return Utils::get_ensure_upload_dir( $path );
	}

	/**
	 * Validate active assets before copying an icon ZIP into same-origin uploads.
	 *
	 * Fonts imported from Fontello, IcoMoon and Fontastic may contain SVG
	 * webfonts and CSS. ZIP entry/path checks do not prevent browser XSS,
	 * remote CSS imports or tracking URL references. Refuse active content
	 * we cannot parse safely instead of publishing an unsafe icon pack.
	 *
	 * @return true|\WP_Error
	 */
	public function validate_public_icon_assets() {
		$root = realpath( $this->directory );
		if ( ! $root || ! is_dir( $root ) || is_link( $this->directory ) ) {
			return new \WP_Error( 'invalid_icon_assets', esc_html__( 'Invalid icon asset directory.', 'elementor-pro' ) );
		}

		$iterator = new \RecursiveIteratorIterator(
			new \RecursiveDirectoryIterator( $root, \FilesystemIterator::SKIP_DOTS )
		);
		$scanned = 0;
		foreach ( $iterator as $asset ) {
			if ( ++$scanned > 4096 || $asset->isLink() ) {
				return new \WP_Error( 'invalid_icon_assets', esc_html__( 'Unsafe icon asset directory.', 'elementor-pro' ) );
			}
			if ( ! $asset->isFile() ) {
				continue;
			}
			$extension = strtolower( pathinfo( $asset->getFilename(), PATHINFO_EXTENSION ) );
			if ( ! in_array( $extension, [ 'css', 'svg' ], true ) ) {
				continue;
			}
			$size = $asset->getSize();
			if ( $size < 1 || $size > 2 * 1024 * 1024 ) {
				return new \WP_Error( 'invalid_icon_assets', esc_html__( 'Icon stylesheet or SVG is invalid or oversized.', 'elementor-pro' ) );
			}
			$data = file_get_contents( $asset->getPathname() );
			$valid = 'css' === $extension
				? self::is_safe_icon_stylesheet( $data, $asset->getPathname(), $root )
				: self::is_safe_svg_font_asset( $data );
			if ( ! $valid ) {
				return new \WP_Error( 'invalid_icon_assets', esc_html__( 'Icon pack contains unsafe CSS or SVG content.', 'elementor-pro' ) );
			}
		}
		return true;
	}

	private static function is_safe_icon_stylesheet( $css, $filename, $root ) {
		if ( ! is_string( $css ) || '' === trim( $css ) || false !== strpos( $css, "\0" )
			|| preg_match( '~@(?:import|namespace)\b|expression\s*\(|(?:-moz-binding|behavior)\s*:|(?:javascript|vbscript|data)\s*:~i', $css ) ) {
			return false;
		}
		// Resolve exactly the CSS url() tokens. Unsupported quoting and CSS
		// escapes fail closed, so escaping cannot turn a remote URL into a
		// path that merely looks relative to our simple parser.
		$tokens = preg_match_all( '~url\s*\(~i', $css );
		$parsed = preg_match_all(
			'~url\s*\(\s*(?:"([^"]*)"|\'([^\']*)\'|([^)]*))\s*\)~i',
			$css, $matches, PREG_SET_ORDER
		);
		if ( false === $tokens || false === $parsed || $tokens !== $parsed ) {
			return false;
		}
		$root = trailingslashit( $root );
		foreach ( $matches as $match ) {
			$reference = trim( '' !== ( $match[1] ?? '' ) ? $match[1]
				: ( '' !== ( $match[2] ?? '' ) ? $match[2] : ( $match[3] ?? '' ) ) );
			if ( ! preg_match( '~^[A-Za-z0-9_./-]+(?:\?[A-Za-z0-9_=&%-]+)?(?:\#[A-Za-z0-9_-]+)?$~D', $reference )
				|| false !== strpos( $reference, '\\' ) || str_starts_with( $reference, '/' ) ) {
				return false;
			}
			$relative = preg_split( '/[?#]/', $reference, 2 )[0];
			$resolved = realpath( dirname( $filename ) . '/' . $relative );
			$extension = strtolower( pathinfo( $relative, PATHINFO_EXTENSION ) );
			if ( ! $resolved || is_link( $resolved ) || ! is_file( $resolved )
				|| ! str_starts_with( $resolved, $root )
				|| ! in_array( $extension, [ 'woff2', 'woff', 'ttf', 'otf', 'eot', 'svg' ], true ) ) {
				return false;
			}
		}
		return true;
	}

	/**
	 * Legacy SVG webfonts cannot pass Elementor's normal icon-image sanitizer,
	 * because their <font>/<glyph> elements are intentionally different.
	 * Keep only the inert SVG *font* vocabulary; never allow scripts, foreign
	 * objects, event handlers, URL attributes, external entities or styles.
	 */
	private static function is_safe_svg_font_asset( $svg ) {
		if ( ! is_string( $svg ) || false !== stripos( $svg, '<!DOCTYPE' )
			|| false !== stripos( $svg, '<!ENTITY' ) || false !== strpos( $svg, "\0" )
			|| ! class_exists( '\DOMDocument' ) ) {
			return false;
		}
		$old_errors = libxml_use_internal_errors( true );
		try {
			$dom = new \DOMDocument();
			if ( ! $dom->loadXML( $svg, LIBXML_NONET | LIBXML_NOERROR | LIBXML_NOWARNING )
				|| $dom->doctype || ! $dom->documentElement
				|| 'svg' !== $dom->documentElement->localName
				|| 'http://www.w3.org/2000/svg' !== $dom->documentElement->namespaceURI ) {
				return false;
			}
			$allowed_elements = [ 'svg', 'defs', 'font', 'font-face', 'glyph',
				'missing-glyph', 'metadata', 'title', 'desc', 'hkern', 'vkern' ];
			$allowed_attributes = [ 'xmlns', 'version', 'id', 'horiz-adv-x',
				'vert-adv-y', 'vert-adv-x', 'glyph-name', 'unicode', 'd',
				'font-family', 'font-weight', 'font-style', 'font-stretch',
				'units-per-em', 'ascent', 'descent', 'x-height', 'cap-height',
				'underline-position', 'underline-thickness', 'bbox',
				'stemv', 'stemh', 'slope', 'accent-height', 'panose-1',
				'font-variant', 'font-size', 'k', 'u1', 'u2', 'g1', 'g2' ];
			$has_font = false;
			$nodes = [ $dom->documentElement ];
			while ( $nodes ) {
				$node = array_pop( $nodes );
				if ( XML_ELEMENT_NODE !== $node->nodeType
					|| 'http://www.w3.org/2000/svg' !== $node->namespaceURI
					|| ! in_array( $node->localName, $allowed_elements, true ) ) {
					return false;
				}
				if ( 'font' === $node->localName ) {
					$has_font = true;
				}
				foreach ( $node->attributes as $attribute ) {
					if ( 'http://www.w3.org/2000/xmlns/' === $attribute->namespaceURI ) {
						if ( ! in_array( $attribute->value, [
							'http://www.w3.org/2000/svg', 'http://www.w3.org/1999/xlink'
						], true ) ) {
							return false;
						}
						continue;
					}
					if ( '' !== (string) $attribute->namespaceURI
						|| ! in_array( $attribute->name, $allowed_attributes, true )
						|| preg_match( '~(?:url\s*\(|javascript:|data:|vbscript:|<)~i', $attribute->value ) ) {
						return false;
					}
				}
				foreach ( $node->childNodes as $child ) {
					if ( XML_ELEMENT_NODE === $child->nodeType ) {
						$nodes[] = $child;
					} elseif ( ! in_array( $child->nodeType, [
						XML_TEXT_NODE, XML_COMMENT_NODE, XML_CDATA_SECTION_NODE
					], true ) ) {
						return false;
					}
				}
			}
			return $has_font;
		} finally {
			libxml_clear_errors();
			libxml_use_internal_errors( $old_errors );
		}
	}

	public function move_files( $post_id ) {
		// @todo: save only needed files
		$wp_filesystem = Custom_Icons::get_wp_filesystem();
		$to = $this->get_ensure_upload_dir( $this->dir_name ) . '/';

		foreach ( $wp_filesystem->dirlist( $this->directory, false, true ) as $file ) {
			// Some third-party icon packs include demo HTML. Fontastic
			// needs its reference HTML only *during parsing*; once the
			// icon config has been prepared, publishing that HTML in
			// same-origin uploads is unnecessary and can introduce XSS
			// through an untrusted demo page.
			if ( preg_match( '/\\.html?$/i', $file['name'] ) ) {
				continue;
			}
			$full_path = $this->directory . $file['name'];
			if ( $wp_filesystem->is_dir( $full_path ) ) {
				$wp_filesystem->mkdir( $to . $file['name'] );

				foreach ( $file['files'] as $filename => $sub_file ) {
					if ( preg_match( '/\\.html?$/i', $filename ) ) {
						continue;
					}
					$new_path = $to . $file['name'] . DIRECTORY_SEPARATOR . $filename;
					$wp_filesystem->move( $full_path . DIRECTORY_SEPARATOR . $filename, $new_path );
					$this->insert_attachment( $this->get_url() . '/' . $file['name'] . '/' . $filename, $new_path, $post_id );
				}
			} else {
				$new_path = $to . $file['name'];
				$wp_filesystem->move( $full_path, $new_path );
				$this->insert_attachment( $this->get_url() . '/' . $file['name'], $new_path, $post_id );
			}
		}

		$this->cleanup_temp_files( $wp_filesystem );
		update_post_meta( $post_id, '_elementor_icon_set_path', $to );
		$this->directory = $to;
	}

	private function insert_attachment( $file_url, $filename, $post_id = 0 ) {
		$attachment = [
			'file' => $filename,
			'guid' => $file_url,
			'post_parent' => $post_id,
			'post_type' => 'attachment',
		];
		$id = wp_insert_attachment( $attachment );
		return $id;
	}

	/**
	 * Names that start with "fa-" are routed to the Font Awesome resolver, so a pack with such a name never renders.
	 *
	 * @return true|\WP_Error
	 */
	public function validate_name() {
		$name = $this->get_name();

		if ( ! is_string( $name ) || '' === trim( $name ) ) {
			return new \WP_Error(
				'invalid_pack_name',
				esc_html__( 'Icon set has no valid name. Check the icon pack export.', 'elementor-pro' )
			);
		}

		if ( preg_match( '#[/\\\\\0]|\.\.#', $name ) ) {
			return new \WP_Error(
				'invalid_pack_name',
				esc_html__( 'The icon set name contains characters that are not allowed. Rename the pack and upload it again.', 'elementor-pro' )
			);
		}

		if ( str_starts_with( strtolower( trim( $name ) ), self::RESERVED_NAME_PREFIX ) ) {
			return new \WP_Error(
				'reserved_pack_name',
				sprintf(
					/* translators: 1: Icon set name, 2: Reserved prefix. */
					esc_html__( 'The icon set name "%1$s" starts with "%2$s", which is reserved for Font Awesome. Rename the pack and upload it again.', 'elementor-pro' ),
					esc_html( $name ),
					self::RESERVED_NAME_PREFIX
				)
			);
		}

		return true;
	}

	public function get_unique_name() {
		$name = $this->get_name();
		$basename = $name;
		$counter = 1;
		while ( ! $this->is_name_unique( $name ) ) {
			$name = $basename . '-' . $counter;
			$counter++;
		}
		return $name;
	}

	private function is_name_unique( $name ) {
		return ! is_dir( $this->get_icon_sets_dir() . '/' . $name );
	}

	protected function get_url( $filename = '' ) {
		return $this->get_file_url( $this->dir_name . $filename );
	}

	protected function get_stylesheet() {
		return '';
	}

	protected function get_version() {
		return '1.0.0';
	}

	protected function get_enqueue() {
		return false;
	}

	/**
	 * Refuse corrupted icon exports before moving files into public uploads.
	 * A source pack containing the required filenames is not necessarily a
	 * valid icon pack: malformed CSS or JSON can produce false/null icon lists.
	 */
	public function validate_icon_contents() {
		$icons = $this->extract_icon_list();
		$prefix = $this->get_prefix();
		if ( ! is_array( $icons ) || empty( $icons )
			|| count( $icons ) > 8192
			|| ! is_string( $prefix ) || '' === trim( $prefix ) ) {
			return new \WP_Error(
				'invalid_icon_contents',
				esc_html__( 'Invalid icon pack stylesheet or icon list.', 'elementor-pro' )
			);
		}
		foreach ( $icons as $name ) {
			if ( ! is_string( $name ) || '' === trim( $name ) || strlen( $name ) > 255 ) {
				return new \WP_Error(
					'invalid_icon_contents',
					esc_html__( 'The icon pack contains an invalid icon name.', 'elementor-pro' )
				);
			}
		}
		return true;
	}

	public function build_config() {
		$icon_set_config = [
			'name' => $this->dir_name,
			'label' => ucwords( str_replace( [ '-', '_' ], ' ', $this->dir_name ) ),
			'url' => $this->get_stylesheet(),
			'enqueue' => $this->get_enqueue(),
			'prefix' => $this->get_prefix(),
			'displayPrefix' => $this->get_display_prefix(),
			'labelIcon' => 'eicon eicon-folder',
			'ver' => $this->get_version(),
			'custom_icon_type' => $this->get_type(),
		];

		$icons = $this->extract_icon_list();
		if ( ! is_array( $icons ) ) {
			return new \WP_Error(
				'invalid_icon_contents',
				esc_html__( 'The icon pack could not be read.', 'elementor-pro' )
			);
		}
		$icon_set_config['count'] = count( $icons );
		$icon_set_config['icons'] = $icons;

		if ( 25 < $icon_set_config['count'] ) {
			$icon_set_config['fetchJson'] = $this->store_icon_list_json( $icons );
		}

		return $icon_set_config;
	}

	private function store_icon_list_json( $icons ) {
		$wp_filesystem = Custom_Icons::get_wp_filesystem();
		$json_file = $this->get_ensure_upload_dir( $this->dir_name ) . '/e_icons.js';
		$wp_filesystem->put_contents( $json_file, json_encode( [ 'icons' => $icons ] ) );
		return $this->get_url() . '/e_icons.js';
	}

	/**
	 * Icon Set Base constructor.
	 *
	 * @param $directory
	 */
	public function __construct( $directory ) {
		$this->directory = $directory;
		return $this->is_icon_set() ? $this : false;
	}
}
