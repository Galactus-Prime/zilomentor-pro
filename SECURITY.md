# Security policy

ZiloMentor Pro is in a **development preview** phase and has not passed
production readiness tests. It must not be installed onto live stores.

The fork incorporates code originally from Elementor Ltd. and PRO Elements,
with its own modifications. Security fixes need to be tracked from both
upstream sources, reviewed, and tested before integration.

Please report potential vulnerabilities privately to the repository owner via
GitHub's private vulnerability reporting feature when available. Do not post
secrets, exploit details, customer data, or credentials in public issues.

Any release must pass automated static checks, a PHP runtime compatibility
matrix, a clean staging WordPress test, and a non-destructive WooCommerce
checkout test with sandbox payment methods.
