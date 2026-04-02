<?php

declare(strict_types=1);

namespace CarFinder;

use RuntimeException;

/**
 * Thrown when catalog data is missing, invalid, or a lookup fails.
 */
final class CatalogException extends RuntimeException
{
}
