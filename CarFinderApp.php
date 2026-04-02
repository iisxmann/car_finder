<?php

declare(strict_types=1);

namespace CarFinder;

/**
 * Interactive flow: pick a brand, then a model, then show vehicle details.
 */
final class CarFinderApp
{
    public function __construct(
        private readonly CatalogService $catalog,
        private readonly Terminal $terminal,
    ) {
    }

    public function run(): int
    {
        try {
            $this->terminal->writeln('');
            $this->terminal->writeln('=== Car Finder (JSON catalog) ===');
            $this->terminal->writeln('Type a brand name or number from the list. Commands: quit, exit, q');
            $this->terminal->writeln('');

            while (true) {
                $brands = $this->catalog->listBrands();
                if ($brands === []) {
                    $this->terminal->writeln('No brands found in the catalog.');
                    return 1;
                }

                $this->printNumberedList('Available brands', $brands);
                $brandInput = $this->terminal->readLine('Brand> ');
                if ($this->isQuit($brandInput)) {
                    $this->terminal->writeln('Goodbye.');
                    return 0;
                }
                if ($brandInput === '') {
                    $this->terminal->writeln('Please enter a brand name or list index.');
                    continue;
                }

                $brandChoice = $this->resolveChoice($brandInput, $brands);
                if ($brandChoice === null) {
                    $this->terminal->writeln('Unknown brand. Try again or use a number from the list.');
                    continue;
                }

                $models = $this->catalog->listModels($brandChoice);
                if ($models === []) {
                    $this->terminal->writeln('No models listed for this brand.');
                    continue;
                }

                $this->printNumberedList('Models for ' . $brandChoice, $models);
                $modelInput = $this->terminal->readLine('Model> ');
                if ($this->isQuit($modelInput)) {
                    $this->terminal->writeln('Goodbye.');
                    return 0;
                }
                if ($modelInput === '') {
                    $this->terminal->writeln('Please enter a model name or list index.');
                    continue;
                }

                $modelChoice = $this->resolveChoice($modelInput, $models);
                if ($modelChoice === null) {
                    $this->terminal->writeln('Unknown model. Try again or use a number from the list.');
                    continue;
                }

                $vehicle = $this->catalog->getVehicle($brandChoice, $modelChoice);
                if ($vehicle === null) {
                    $this->terminal->writeln('Could not load vehicle details.');
                    continue;
                }

                $this->terminal->writeln('');
                $this->terminal->writeln('--- Vehicle details ---');
                $this->terminal->writeln('Brand : ' . $vehicle->brand);
                $this->terminal->writeln('Model : ' . $vehicle->model);
                $this->terminal->writeln('Engine: ' . $vehicle->engine);
                $this->terminal->writeln('Power : ' . $vehicle->hp . ' hp');
                $this->terminal->writeln('Fuel  : ' . $vehicle->fuel);
                $this->terminal->writeln('-----------------------');
                $this->terminal->writeln('');
            }
        } catch (CatalogException $e) {
            $this->terminal->writeln('Error: ' . $e->getMessage());
            return 1;
        }
    }

    /**
     * @param list<string> $items
     */
    private function printNumberedList(string $title, array $items): void
    {
        $this->terminal->writeln($title . ':');
        $i = 1;
        foreach ($items as $name) {
            $this->terminal->writeln(sprintf('  [%d] %s', $i, $name));
            ++$i;
        }
        $this->terminal->writeln('');
    }

    /**
     * @param list<string> $items
     */
    private function resolveChoice(string $input, array $items): ?string
    {
        if (preg_match('/^\d+$/', $input) === 1) {
            $idx = (int) $input;
            if ($idx >= 1 && $idx <= count($items)) {
                return $items[$idx - 1];
            }
            return null;
        }

        $needle = strtolower(trim($input));
        foreach ($items as $name) {
            if (strtolower($name) === $needle) {
                return $name;
            }
        }

        foreach ($items as $name) {
            if (str_contains(strtolower($name), $needle)) {
                return $name;
            }
        }

        return null;
    }

    private function isQuit(string $input): bool
    {
        $n = strtolower(trim($input));
        return $n === 'q' || $n === 'quit' || $n === 'exit';
    }
}
