#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * CLI entry: run from project root: php carfinder.php
 */

require __DIR__ . '/autoload.php';

use CarFinder\CarFinderApp;
use CarFinder\CatalogService;
use CarFinder\Config;
use CarFinder\JsonCarRepository;
use CarFinder\Terminal;

$repository = new JsonCarRepository(Config::dataPath());
$catalog = new CatalogService($repository);
$app = new CarFinderApp($catalog, new Terminal());

exit($app->run());
