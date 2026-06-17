const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log(`Deploying with account: ${deployer.address}`);
  console.log(`Network: ${hre.network.name}`);

  const ModelRegistry = await hre.ethers.getContractFactory("ModelRegistry");
  const registry = await ModelRegistry.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  const deploymentTx = registry.deploymentTransaction();

  console.log(`ModelRegistry deployed to: ${address}`);
  if (deploymentTx) {
    console.log(`Deployment transaction: ${deploymentTx.hash}`);
  }

  const outputDir = path.join(__dirname, "../../artifacts");
  fs.mkdirSync(outputDir, { recursive: true });

  const deploymentInfo = {
    network: hre.network.name,
    contractName: "ModelRegistry",
    contractAddress: address,
    deployer: deployer.address,
    deploymentTransaction: deploymentTx ? deploymentTx.hash : null,
    deployedAt: new Date().toISOString(),
    explorerUrl:
      hre.network.name === "sepolia"
        ? `https://sepolia.etherscan.io/address/${address}`
        : null
  };

  fs.writeFileSync(
    path.join(outputDir, `deployment-${hre.network.name}.json`),
    JSON.stringify(deploymentInfo, null, 2)
  );

  fs.writeFileSync(
    path.join(outputDir, "deployment-latest.json"),
    JSON.stringify(deploymentInfo, null, 2)
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
