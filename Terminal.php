<?php

declare(strict_types=1);

namespace CarFinder;

/**
 * Minimal stdin/stdout helpers for the interactive CLI.
 */
final class Terminal
{
    public function writeln(string $line = ''): void
    {
        fwrite(STDOUT, $line . PHP_EOL);
    }

    public function write(string $text): void
    {
        fwrite(STDOUT, $text);
    }

    public function readLine(string $prompt): string
    {
        $this->write($prompt);
        $line = fgets(STDIN);
        if ($line === false) {
            return '';
        }
        return trim($line);
    }
}
