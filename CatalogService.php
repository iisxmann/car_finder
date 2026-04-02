<?php

declare(strict_types=1);

namespace CarFinder;

/**
 * High-level catalog operations used by the CLI (brands, models, full spec).
 */
final class CatalogService
{
    public function __construct(
        private readonly JsonCarRepository $repository,
    ) {
    }

    /**
     * @return list<string>
     */
    public function listBrands(): array
    {
        return $this->repository->brandNames();
    }

    /**
     * @return list<string>
     */
    public function listModels(string $brandQuery): array
    {
        return $this->repository->modelNamesForBrand($brandQuery);
    }

    public function getVehicle(string $brandQuery, string $modelQuery): ?VehicleSpec
    {
        $row = $this->repository->resolveVehicle($brandQuery, $modelQuery);
        if ($row === null) {
            return null;
        }

        return new VehicleSpec(
            brand: $row['brand'],
            model: $row['model'],
            engine: $row['engine'],
            hp: $row['hp'],
            fuel: $row['fuel'],
        );
    }
}
