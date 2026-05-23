// Imports the Hardhat Runtime Environment.
const hre = require("hardhat");

// Main deployment function.
async function main() {
  // Loads the compiled ModelRegistry contract factory.
  const ModelRegistry = await hre.ethers.getContractFactory("ModelRegistry");
  // Deploys a new instance of the ModelRegistry smart contract.
  const registry = await ModelRegistry.deploy();
  // Waits until the contract deployment is confirmed.
  await registry.waitForDeployment();

  // Prints the deployed contract address to the terminal.
  console.log(`ModelRegistry deployed to: ${await registry.getAddress()}`);
}

// Executes main() and handles any deployment errors.
main().catch((error) => {
  // Prints the error details.
  console.error(error);
  // Sets a non-zero process exit code to indicate failure.
  process.exitCode = 1;
});
