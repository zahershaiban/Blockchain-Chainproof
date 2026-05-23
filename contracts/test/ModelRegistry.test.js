// Imports expect from Chai for writing assertions.
const { expect } = require("chai");
// Imports ethers from Hardhat for deploying and interacting with contracts.
const { ethers } = require("hardhat");

// Groups tests for the ModelRegistry contract.
describe("ModelRegistry", function () {
  // Defines one test case for registering and reading a model record.
  it("registers and returns a model record", async function () {
    // Loads the compiled ModelRegistry contract factory.
    const ModelRegistry = await ethers.getContractFactory("ModelRegistry");
    // Deploys a fresh ModelRegistry contract for this test.
    const registry = await ModelRegistry.deploy();
    // Waits until deployment is finished.
    await registry.waitForDeployment();

    // Calls registerModel to save a sample model record.
    await registry.registerModel(
      // Sample record/model ID.
      "LoanRiskClassifier",
      // Sample model version.
      "1.0.0",
      // Sample dataset hash from the older version of the project.
      "datasetHash",
      // Sample trained model file hash.
      "modelHash",
      // Sample config file hash.
      "configHash"
    );

    // Reads back a model record from the contract.
    const record = await registry.getModel(0);
    // Checks that the returned model name matches the expected value.
    expect(record.modelName).to.equal("LoanRiskClassifier");
    // Checks that the returned version matches the expected value.
    expect(record.version).to.equal("1.0.0");
    // Checks that the returned dataset hash matches the expected value.
    expect(record.datasetHash).to.equal("datasetHash");
  });
});
