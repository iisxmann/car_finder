<?php

declare(strict_types=1);

namespace CarFinder;

/**
 * Immutable vehicle specification row from JSON (engine, hp, fuel).
 */
final class VehicleSpec
{
    public function __construct(
        public readonly string $brand,
        public readonly string $model,
        public readonly string $engine,
        public readonly string $hp,
        public readonly string $fuel,
    ) {
    }
}
