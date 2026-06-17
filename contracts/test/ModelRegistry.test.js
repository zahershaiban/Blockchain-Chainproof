const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ModelRegistry", function () {
  async function deployRegistry() {
    const ModelRegistry = await ethers.getContractFactory("ModelRegistry");
    const registry = await ModelRegistry.deploy();
    await registry.waitForDeployment();
    return registry;
  }

  it("registers and returns a model record", async function () {
    const registry = await deployRegistry();

    await registry.registerModel(
      "HealthRiskClassifier-1.0.0",
      "Health Risk Classifier",
      "1.0.0",
      "datasetMerkleRoot",
      "modelHash",
      "configHash"
    );

    const record = await registry.getModel("HealthRiskClassifier-1.0.0");

    expect(record.recordId).to.equal("HealthRiskClassifier-1.0.0");
    expect(record.modelName).to.equal("Health Risk Classifier");
    expect(record.version).to.equal("1.0.0");
    expect(record.datasetMerkleRoot).to.equal("datasetMerkleRoot");
    expect(record.modelHash).to.equal("modelHash");
    expect(record.configHash).to.equal("configHash");
  });

  it("prevents duplicate record IDs", async function () {
    const registry = await deployRegistry();

    await registry.registerModel(
      "HealthRiskClassifier-1.0.0",
      "Health Risk Classifier",
      "1.0.0",
      "datasetMerkleRoot",
      "modelHash",
      "configHash"
    );

    await expect(
      registry.registerModel(
        "HealthRiskClassifier-1.0.0",
        "Health Risk Classifier",
        "1.0.0",
        "datasetMerkleRoot",
        "modelHash",
        "configHash"
      )
    ).to.be.revertedWith("record already exists");
  });

  it("stores version history for one model name", async function () {
    const registry = await deployRegistry();

    await registry.registerModel("HealthRiskClassifier-1.0.0", "Health Risk Classifier", "1.0.0", "root1", "model1", "config1");
    await registry.registerModel("HealthRiskClassifier-1.1.0", "Health Risk Classifier", "1.1.0", "root2", "model2", "config2");

    const history = await registry.getModelHistory("Health Risk Classifier");
    const latest = await registry.getLatestModel("Health Risk Classifier");

    expect(history.length).to.equal(2);
    expect(history[0]).to.equal("HealthRiskClassifier-1.0.0");
    expect(history[1]).to.equal("HealthRiskClassifier-1.1.0");
    expect(latest.version).to.equal("1.1.0");
    expect(await registry.getVersionCount("Health Risk Classifier")).to.equal(2);
    expect(await registry.getTotalRecords()).to.equal(2);
  });

  it("rejects empty required fields", async function () {
    const registry = await deployRegistry();

    await expect(
      registry.registerModel("", "Health Risk Classifier", "1.0.0", "root", "model", "config")
    ).to.be.revertedWith("recordId required");
  });
});
