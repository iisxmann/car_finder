<?php

declare(strict_types=1);

namespace CarFinder;

/**
 * Loads and exposes the JSON vehicle catalog: brands, models, and specs.
 */
final class JsonCarRepository
{
    /** @var array<string, array<string, array{engine: string, hp: string, fuel: string}>>|null */
    private ?array $cache = null;

    public function __construct(
        private readonly string $jsonFilePath,
    ) {
    }

    /**
     * @return array<string, array<string, array{engine: string, hp: string, fuel: string}>>
     */
    public function all(): array
    {
        if ($this->cache !== null) {
            return $this->cache;
        }

        if (!is_readable($this->jsonFilePath)) {
            throw new CatalogException('Vehicle data file is missing or not readable: ' . $this->jsonFilePath);
        }

        $raw = file_get_contents($this->jsonFilePath);
        if ($raw === false) {
            throw new CatalogException('Failed to read vehicle data file.');
        }

        $decoded = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($decoded)) {
            throw new CatalogException('Vehicle data must be a JSON object keyed by brand.');
        }

        $this->cache = $this->normalizeCatalog($decoded);
        return $this->cache;
    }

    /**
     * @param array<mixed, mixed> $decoded
     * @return array<string, array<string, array{engine: string, hp: string, fuel: string}>>
     */
    private function normalizeCatalog(array $decoded): array
    {
        $out = [];
        foreach ($decoded as $brand => $models) {
            if (!is_string($brand) || !is_array($models)) {
                continue;
            }
            $brandKey = trim($brand);
            if ($brandKey === '') {
                continue;
            }
            $out[$brandKey] = [];
            foreach ($models as $modelName => $spec) {
                if (!is_string($modelName) || !is_array($spec)) {
                    continue;
                }
                $modelKey = trim($modelName);
                if ($modelKey === '') {
                    continue;
                }
                $engine = isset($spec['engine']) && is_string($spec['engine']) ? trim($spec['engine']) : '';
                $hp = isset($spec['hp']) && is_string($spec['hp']) ? trim($spec['hp']) : '';
                $fuel = isset($spec['fuel']) && is_string($spec['fuel']) ? trim($spec['fuel']) : '';
                $out[$brandKey][$modelKey] = [
                    'engine' => $engine,
                    'hp' => $hp,
                    'fuel' => $fuel,
                ];
            }
        }

        return $out;
    }

    /**
     * @return list<string>
     */
    public function brandNames(): array
    {
        $names = array_keys($this->all());
        sort($names, SORT_STRING);
        return array_values($names);
    }

    /**
     * @return list<string>
     */
    public function modelNamesForBrand(string $brand): array
    {
        $catalog = $this->all();
        $key = $this->resolveBrandKey($brand, $catalog);
        if ($key === null || !isset($catalog[$key])) {
            return [];
        }
        $models = array_keys($catalog[$key]);
        sort($models, SORT_STRING);
        return array_values($models);
    }

    /**
     * @param array<string, mixed> $catalog
     */
    private function resolveBrandKey(string $input, array $catalog): ?string
    {
        $trim = trim($input);
        if ($trim === '') {
            return null;
        }
        if (array_key_exists($trim, $catalog)) {
            return $trim;
        }
        $lower = strtolower($trim);
        foreach (array_keys($catalog) as $name) {
            if (strtolower($name) === $lower) {
                return $name;
            }
        }
        return null;
    }

    public function findSpec(string $brand, string $model): ?array
    {
        $row = $this->resolveVehicle($brand, $model);
        if ($row === null) {
            return null;
        }
        return [
            'engine' => $row['engine'],
            'hp' => $row['hp'],
            'fuel' => $row['fuel'],
        ];
    }

    /**
     * @return array{brand: string, model: string, engine: string, hp: string, fuel: string}|null
     */
    public function resolveVehicle(string $brand, string $model): ?array
    {
        $catalog = $this->all();
        $b = $this->resolveBrandKey($brand, $catalog);
        if ($b === null || !isset($catalog[$b])) {
            return null;
        }
        $models = $catalog[$b];
        $m = $this->resolveModelKey($model, $models);
        if ($m === null) {
            return null;
        }
        $spec = $models[$m];
        return [
            'brand' => $b,
            'model' => $m,
            'engine' => $spec['engine'],
            'hp' => $spec['hp'],
            'fuel' => $spec['fuel'],
        ];
    }

    /**
     * @param array<string, array{engine: string, hp: string, fuel: string}> $models
     */
    private function resolveModelKey(string $input, array $models): ?string
    {
        $trim = trim($input);
        if ($trim === '') {
            return null;
        }
        if (array_key_exists($trim, $models)) {
            return $trim;
        }
        $lower = strtolower($trim);
        foreach (array_keys($models) as $name) {
            if (strtolower($name) === $lower) {
                return $name;
            }
        }
        return null;
    }
}
