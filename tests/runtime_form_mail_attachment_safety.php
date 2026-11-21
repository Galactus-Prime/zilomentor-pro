<?php
/**
 * Exercise classic Form Email attachment read/cleanup path restrictions.
 * Only synthetic disposable WordPress with ZMP_ISOLATED_QA=yes.
 */
if ( ! defined( 'ABSPATH' ) || 'yes' !== getenv( 'ZMP_ISOLATED_QA' ) ) {
	exit( 2 );
}

$utility = '\ElementorPro\Core\Utils';
$record_class = '\ElementorPro\Modules\Forms\Classes\Form_Record';
$email_class = '\ElementorPro\Modules\Forms\Actions\Email';
$upload_class = '\ElementorPro\Modules\Forms\Fields\Upload';

foreach ( [ $utility, $record_class, $email_class, $upload_class ] as $class ) {
	if ( ! class_exists( $class ) ) {
		throw new \RuntimeException( 'Required isolated Form class missing: ' . $class );
	}
}

$uploads = wp_upload_dir( null, false );
$root = trailingslashit( $uploads['basedir'] ) . 'elementor/forms';
wp_mkdir_p( $root );

$checks = [];
$qa_name = 'zmp-mail-' . wp_generate_password( 14, false, false ) . '.txt';
$good = trailingslashit( $root ) . $qa_name;
$outer = trailingslashit( $uploads['basedir'] ) . 'zmp-outside-' . wp_generate_password( 14, false, false ) . '.txt';
$nested = trailingslashit( $root ) . 'zmp-subdir-' . wp_generate_password( 12, false, false );
$link = trailingslashit( $root ) . 'zmp-symlink-' . wp_generate_password( 12, false, false );
$custom = trailingslashit( $uploads['basedir'] ) . 'zmp-owner-forms-' . wp_generate_password( 12, false, false );
$custom_file = trailingslashit( $custom ) . 'owner-file.txt';
$filter = static function( $path ) use ( $custom ) { return $custom; };
$linked = false;

file_put_contents( $good, 'safe synthetic mail attachment' );
file_put_contents( $outer, 'do not attach or delete this external file' );
wp_mkdir_p( $nested );
wp_mkdir_p( $custom );
file_put_contents( $custom_file, 'approved synthetic custom attachment' );
try {
	$checks['form_mail_allows_direct_upload_file'] = $utility::is_safe_form_attachment_path( $good );
	$checks['form_mail_rejects_external_upload_path'] = ! $utility::is_safe_form_attachment_path( $outer );
	$checks['form_mail_rejects_upload_root'] = ! $utility::is_safe_form_attachment_path( $root );
	$checks['form_mail_rejects_missing_or_array_paths'] =
		! $utility::is_safe_form_attachment_path( $root . '/missing.txt' )
		&& ! $utility::is_safe_form_attachment_path( [ $good ] );
	$checks['form_mail_rejects_nested_upload_file'] = ! $utility::is_safe_form_attachment_path( $nested );
	$linked = function_exists( 'symlink' ) && @symlink( $outer, $link );
	$checks['form_mail_rejects_symlink_file'] = ! $linked || ! $utility::is_safe_form_attachment_path( $link );

	$record = ( new \ReflectionClass( $record_class ) )->newInstanceWithoutConstructor();
	$record->set( 'files', [
		'email_field' => [
			'path' => [ $good, $outer, $root . '/missing.txt', [ $outer ] ],
		],
	] );
	$email = ( new \ReflectionClass( $email_class ) )->newInstanceWithoutConstructor();
	$collector = ( new \ReflectionClass( $email_class ) )->getMethod( 'get_file_by_attachment_type' );
	$fields = [ [ 'custom_id' => 'email_field', 'attachment_type' => $upload_class::MODE_ATTACH ] ];
	$collected = $collector->invoke( $email, $fields, $record, $upload_class::MODE_ATTACH );
	// Elementor's Collection::values() may return an array directly.
	$paths = is_object( $collected ) && method_exists( $collected, 'all' )
		? array_values( $collected->all() ) : array_values( (array) $collected );
	$checks['email_action_refuses_external_and_malformed_paths'] =
		[ $good ] === $paths;
	$checks['email_action_did_not_delete_unrelated_file'] =
		file_get_contents( $outer ) === 'do not attach or delete this external file';

	add_filter( 'elementor_pro/forms/upload_path', $filter );
	try {
		$checks['form_mail_honours_owner_configured_path'] =
			$utility::is_safe_form_attachment_path( $custom_file )
			&& ! $utility::is_safe_form_attachment_path( $good );
	} finally {
		remove_filter( 'elementor_pro/forms/upload_path', $filter );
	}
} finally {
	foreach ( [ $good, $outer, $custom_file, $link ] as $path ) {
		if ( is_file( $path ) || is_link( $path ) ) {
			@unlink( $path );
		}
	}
	@rmdir( $nested );
	@rmdir( $custom );
}

foreach ( $checks as $name => $passed ) {
	echo ( $passed ? 'PASS ' : 'FAIL ' ) . $name . PHP_EOL;
}
if ( count( $checks ) < 8 || in_array( false, $checks, true ) ) {
	exit( 4 );
}
