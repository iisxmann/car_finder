<?php

declare(strict_types=1);

/**
 * Autoloads CarFinder\* classes from the project root (same directory as this file).
 */
spl_autoload_register(static function (string $class): void {
    $prefix = 'CarFinder\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $relative = substr($class, strlen($prefix));
    $path = __DIR__ . DIRECTORY_SEPARATOR . str_replace('\\', DIRECTORY_SEPARATOR, $relative) . '.php';
    if (is_readable($path)) {
        require $path;
    }
});
