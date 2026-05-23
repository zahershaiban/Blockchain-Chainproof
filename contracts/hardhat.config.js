// Loads the Hardhat toolbox plugin, including ethers, testing tools, and matchers.
require("@nomicfoundation/hardhat-toolbox");

// Exports the Hardhat project configuration.
module.exports = {
  // Selects the Solidity compiler version used for compiling contracts.
  solidity: "0.8.24",
  // Defines blockchain networks that Hardhat can connect to.
  networks: {
    // Configuration for a local Hardhat node.
    localhost: {
      // RPC URL for the local blockchain node.
      url: "http://127.0.0.1:8545"
    }
  }
};
