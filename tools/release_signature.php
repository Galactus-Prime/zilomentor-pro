<?php
/**
 * Manual ZiloMentor Pro Ed25519 detached-release signatures.
 *
 * Run ONLY as a CLI program with PHP Sodium. Keys are never put in WordPress,
 * the ZIP, the repository, or a public directory. No network or Actions.
 *
 * generate PRIVATE_KEY_PATH PUBLIC_KEY_PATH
 * sign     MANIFEST_JSON PRIVATE_KEY_PATH SIGNATURE_PATH
 * verify   MANIFEST_JSON PUBLIC_KEY_PATH SIGNATURE_PATH
 *
 * Private keys must be generated and retained on a trusted OFFLINE machine.
 */
if ( PHP_SAPI !== 'cli' || ! extension_loaded( 'sodium' ) ) {
    fwrite( STDERR, "Requires PHP CLI with Sodium\n" );
    exit( 2 );
}
function zmp_release_abort( $message ) {
    fwrite( STDERR, $message . "\n" );
    exit( 2 );
}
function zmp_release_file( $path, $max = 16384 ) {
    if ( ! is_file( $path ) || is_link( $path ) || filesize( $path ) < 1
        || filesize( $path ) > $max ) {
        zmp_release_abort( 'Invalid input file' );
    }
    $data = file_get_contents( $path );
    if ( false === $data ) {
        zmp_release_abort( 'Unable to read file' );
    }
    return $data;
}
function zmp_release_key( $path, $length, $is_secret = false ) {
    if ( $is_secret && ( fileperms( $path ) & 0077 ) ) {
        zmp_release_abort( 'Private key must have mode 0600' );
    }
    if ( $is_secret && function_exists( 'posix_geteuid' )
        && fileowner( $path ) !== posix_geteuid() ) {
        zmp_release_abort( 'Private key must be owned by current user' );
    }
    $value = base64_decode( trim( zmp_release_file( $path, 256 ) ), true );
    if ( false === $value || strlen( $value ) !== $length ) {
        zmp_release_abort( 'Invalid Ed25519 key encoding' );
    }
    return $value;
}
function zmp_release_write_new( $path, $text ) {
    if ( file_exists( $path ) || is_link( $path ) ) {
        zmp_release_abort( 'Refusing to overwrite existing output' );
    }
    if ( preg_match( '~/(?:public_html|wp-content|htdocs|www)/~i', $path ) ) {
        zmp_release_abort( 'Refusing to write signing files inside a webroot' );
    }
    $old_mask = umask( 0077 );
    $handle = @fopen( $path, 'x' );
    if ( false === $handle ) {
        umask( $old_mask );
        zmp_release_abort( 'Cannot create exclusive output file' );
    }
    $written = fwrite( $handle, $text );
    fclose( $handle );
    umask( $old_mask );
    if ( $written !== strlen( $text ) ) {
        @unlink( $path );
        zmp_release_abort( 'Incomplete output file' );
    }
    chmod( $path, 0600 );
}
if ( count( $argv ) !== 5 && count( $argv ) !== 4 ) {
    zmp_release_abort( 'Usage: generate PRIVATE PUBLIC | sign MANIFEST PRIVATE SIGNATURE | verify MANIFEST PUBLIC SIGNATURE' );
}
$operation = $argv[1];
if ( 'generate' === $operation && count( $argv ) === 4 ) {
    $keypair = sodium_crypto_sign_keypair();
    zmp_release_write_new( $argv[2], base64_encode( sodium_crypto_sign_secretkey( $keypair ) ) . "\n" );
    zmp_release_write_new( $argv[3], base64_encode( sodium_crypto_sign_publickey( $keypair ) ) . "\n" );
    sodium_memzero( $keypair );
    echo "PUBLIC_AND_PRIVATE_KEYS_CREATED; KEEP_PRIVATE_KEY_OFFLINE\n";
    exit( 0 );
}
if ( 'sign' === $operation && count( $argv ) === 5 ) {
    $payload = zmp_release_file( $argv[2] );
    $secret = zmp_release_key( $argv[3], SODIUM_CRYPTO_SIGN_SECRETKEYBYTES, true );
    $signature = sodium_crypto_sign_detached( $payload, $secret );
    sodium_memzero( $secret );
    zmp_release_write_new( $argv[4], base64_encode( $signature ) . "\n" );
    echo "MANIFEST_SIGNATURE_CREATED\n";
    exit( 0 );
}
if ( 'verify' === $operation && count( $argv ) === 5 ) {
    $payload = zmp_release_file( $argv[2] );
    $public = zmp_release_key( $argv[3], SODIUM_CRYPTO_SIGN_PUBLICKEYBYTES );
    $signature = base64_decode( trim( zmp_release_file( $argv[4], 256 ) ), true );
    if ( false === $signature || strlen( $signature ) !== SODIUM_CRYPTO_SIGN_BYTES ) {
        zmp_release_abort( 'Invalid signature encoding' );
    }
    if ( ! sodium_crypto_sign_verify_detached( $signature, $payload, $public ) ) {
        zmp_release_abort( 'Ed25519 signature verification failed' );
    }
    echo "VALID_ED25519_RELEASE_SIGNATURE\n";
    exit( 0 );
}
zmp_release_abort( 'Invalid operation or arguments' );
