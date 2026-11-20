<?php
namespace ElementorPro\Modules\Posts\Data;

use Elementor\Utils;
use ElementorPro\Data\Base\Controller as Controller_Base;
use ElementorPro\Plugin;

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

class Controller extends Controller_Base {

	public function get_name() {
		return 'posts-widget';
	}

	public function register_endpoints() {
		// There is only get items end point
	}

	public function get_items( $request ) {
		$document = Plugin::elementor()->documents->get( $request->get_param( 'post_id' ) );

		if ( ! $document ) {
			return new \WP_Error(
				'document_not_exist',
				__( 'Document doesn\'t exist', 'elementor-pro' ),
				[ 'status' => 404 ]
			);
		}

		$element_data = $document->get_elements_data();
		$posts_widget = Utils::find_element_recursive( $element_data, $request->get_param( 'element_id' ) );

		if ( empty( $posts_widget ) || ! is_array( $posts_widget )
			|| ! in_array( $posts_widget['widgetType'] ?? '', [ 'posts', 'portfolio' ], true ) ) {
			return new \WP_Error(
				'Element_not_exist',
				__( 'Posts widget doesn\'t exist', 'elementor-pro' ),
				[ 'status' => 404 ]
			);
		}

		set_query_var( 'paged', $request->get_param( 'page' ) );

		/** @var \ElementorPro\Modules\Posts\Widgets\Posts $element_instance */
		$element_instance = Plugin::elementor()->elements_manager->create_element_instance( $posts_widget );

		ob_start();
		$element_instance->render_content();
		$html = ob_get_clean();

		return [
			'content' => $html,
		];
	}

	public function get_permission_callback( $request ) {
		// Public pagination must never render a draft, private or password-
		// protected Elementor document selected by an anonymous caller.
		// Authenticated editors may still preview documents they can edit.
		$post_id = absint( $request->get_param( 'post_id' ) );
		if ( ! $post_id || ! get_post( $post_id ) ) {
			return false;
		}

		if ( current_user_can( 'edit_post', $post_id ) ) {
			return true;
		}

		return 'publish' === get_post_status( $post_id ) && ! post_password_required( $post_id );
	}
}
