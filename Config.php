<?php

declare(strict_types=1);

namespace CarFinder;

/**
 * Application paths and runtime configuration.
 */
final class Config
{
    public static function projectRoot(): string
    {
        return __DIR__;
    }

    public static function dataPath(): string
    {
        return self::projectRoot() . DIRECTORY_SEPARATOR . 'data' . DIRECTORY_SEPARATOR . 'vehicles.json';
    }
}
