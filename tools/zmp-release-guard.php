<?php
/**
 * Plugin Name: ZiloMentor Release Integrity Guard
 * Description: Blocks ordinary WordPress plugin upgraders from replacing the independently managed ZiloMentor Pro compatibility folder.
 * Version: 0.2.0
 *
 * Install as wp-content/mu-plugins/zmp-release-guard.php, not as part
 * of the elementor-pro folder. Manual SHA256/signed atomic releases do not
 * use WP_Upgrader and remain possible.
 *
 * This does NOT disable vulnerability notifications, scanners, WordPress
 * security updates for other plugins, or filesystem-level/root tools.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

function zmp_release_guard_basenames() {
    // The legacy folder still needs protection during and after migration,
    // because WP Toolkit may try to reinstall a vendor Elementor Pro ZIP.
    return array(
        'elementor-pro/elementor-pro.php',
        'zilomentor-pro/elementor-pro.php',
    );
}

function zmp_release_guard_active() {
    // Look at the real installed headers, not remote vendor update metadata.
    // Support the protected legacy beta and independently named deployments.
    foreach ( zmp_release_guard_basenames() as $basename ) {
        $entry = WP_PLUGIN_DIR . '/' . $basename;
        if ( ! is_file( $entry ) || is_link( $entry ) ) {
            continue;
        }

        $headers = get_file_data( $entry, array( 'Name' => 'Plugin Name', 'UpdateURI' => 'Update URI' ) );
        if ( isset( $headers['Name'], $headers['UpdateURI'] )
            && 'ZiloMentor Pro' === $headers['Name']
            && 'https://github.com/Galactus-Prime/zilomentor-pro' === $headers['UpdateURI'] ) {
            return true;
        }
    }
    return false;
}

function zmp_release_guard_targets_compat( $extra ) {
    if ( ! is_array( $extra ) ) {
        return false;
    }
    $targets = zmp_release_guard_basenames();
    $slugs = array( 'elementor-pro', 'zilomentor-pro' );

    if ( isset( $extra['plugin'] )
        && in_array( $extra['plugin'], array_merge( $targets, $slugs ), true ) ) {
        return true;
    }

    if ( isset( $extra['plugins'] ) && is_array( $extra['plugins'] )
        && array_intersect( $targets, $extra['plugins'] ) ) {
        return true;
    }

    return isset( $extra['slug'] ) && in_array( $extra['slug'], $slugs, true );
}

function zmp_release_guard_block( $result, $extra ) {
    if ( is_wp_error( $result ) || ! zmp_release_guard_active() ) {
        return $result;
    }
    if ( zmp_release_guard_targets_compat( $extra ) ) {
        return new WP_Error(
            'zmp_release_integrity_guard',
            'ZiloMentor Pro is independently managed. Do not replace its elementor-pro folder with an Elementor Pro update; use the signed ZiloMentor release procedure.'
        );
    }
    return $result;
}

function zmp_release_guard_pre_download( $reply, $package, $upgrader, $extra ) {
    // upgrader_pre_download supplies $package before $hook_extra. Keep this
    // wrapper distinct from upgrader_pre_install to avoid argument confusion.
    return zmp_release_guard_block( $reply, $extra );
}
add_filter( 'upgrader_pre_download', 'zmp_release_guard_pre_download', 10, 4 );
add_filter( 'upgrader_pre_install', 'zmp_release_guard_block', 10, 2 );

function zmp_release_guard_source( $source, $remote_source, $upgrader, $extra ) {
    if ( is_wp_error( $source ) || ! zmp_release_guard_active() ) {
        return $source;
    }
    if ( zmp_release_guard_targets_compat( $extra ) ) {
        return zmp_release_guard_block( $source, $extra );
    }
    if ( ! is_string( $source ) || ! is_array( $extra ) || 'plugin' !== ( $extra['type'] ?? '' ) ) {
        return $source;
    }

    // Some ZIP-based installers do not provide the current plugin basename.
    // Inspect the extracted plugin name/path before allowing replacement.
    $folder = basename( untrailingslashit( $source ) );
    if ( in_array( $folder, array( 'elementor-pro', 'zilomentor-pro' ), true )
        || is_file( trailingslashit( $source ) . 'elementor-pro.php' ) ) {
        return new WP_Error(
            'zmp_release_integrity_guard',
            'Installing a plugin into elementor-pro is blocked while ZiloMentor Pro is active. Use a signed, owner-operated manual release.'
        );
    }

    return $source;
}
add_filter( 'upgrader_source_selection', 'zmp_release_guard_source', 10, 4 );

function zmp_release_guard_no_auto_update( $update, $item ) {
    if ( zmp_release_guard_active()
        && is_object( $item )
        && isset( $item->plugin )
        && in_array( $item->plugin, zmp_release_guard_basenames(), true ) ) {
        return false;
    }
    return $update;
}
add_filter( 'auto_update_plugin', 'zmp_release_guard_no_auto_update', 100, 2 );
