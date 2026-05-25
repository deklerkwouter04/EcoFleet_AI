from utils import execute_sql

tables = [
    """
    CREATE TABLE Companies (
        CompanyID INT PRIMARY KEY IDENTITY(1,1),
        CompanyName NVARCHAR(100)
    )
    """,
    """
    CREATE TABLE FleetList (
        VehicleID NVARCHAR(50) PRIMARY KEY,
        CompanyID INT FOREIGN KEY REFERENCES Companies(CompanyID),
        Make NVARCHAR(50),
        Model NVARCHAR(100),
        Registration NVARCHAR(20),
        VIN NVARCHAR(17),
        FuelType NVARCHAR(20),
        InitialCost MONEY,
        PurchaseDate DATE,
        ProjectedTermMonths INT,
        ProjectedKmPerYear FLOAT,
        CurrentKm FLOAT,
        Application NVARCHAR(50),
        CarbonUsage FLOAT -- kg CO2/km
    )
    """,
    """
    CREATE TABLE PartsBasket (
        PartID INT PRIMARY KEY IDENTITY(1,1),
        ComponentName NVARCHAR(100),
        ExpectedLifeKm FLOAT,
        ApplicationType NVARCHAR(50),
        CostPerUnit MONEY
    )
    """,
    """
    CREATE TABLE MaintenanceLogs (
        LogID INT PRIMARY KEY IDENTITY(1,1),
        VehicleID NVARCHAR(50) FOREIGN KEY REFERENCES FleetList(VehicleID),
        ServiceDate DATE,
        ServiceKm FLOAT,
        PartID INT FOREIGN KEY REFERENCES PartsBasket(PartID),
        ActualCost MONEY,
        OilRecoveredLitres FLOAT
    )
    """,
    """
    CREATE TABLE TyreLogs (
        TyreLogID INT PRIMARY KEY IDENTITY(1,1),
        VehicleID NVARCHAR(50),
        TyrePosition NVARCHAR(20),
        InstallDate DATE,
        InstallKm FLOAT,
        RemovalDate DATE,
        RemovalKm FLOAT,
        Cost MONEY
    )
    """,
    """
    CREATE TABLE Inspections (
        InspectionID INT PRIMARY KEY IDENTITY(1,1),
        VehicleID NVARCHAR(50),
        InspectionDate DATE,
        Inspector NVARCHAR(50),
        SANSCompliant BIT,
        AIConfidence FLOAT,
        Notes NVARCHAR(MAX)
    )
    """
]

for table in tables:
    try:
        execute_sql(table)
        print("Table created.")
    except Exception as e:
        print(f"Error: {e}")