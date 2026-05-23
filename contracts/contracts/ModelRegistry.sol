// SPDX-License-Identifier: MIT
// Declares the Solidity compiler version range for this contract.
pragma solidity ^0.8.20;

// Defines the smart contract that stores AI model registration records.
contract ModelRegistry {
    // Defines the structure of one registered model record.
    struct ModelRecord {
        // Human-readable name of the model.
        string modelName;
        // Version of the model registration.
        string version;
        // Merkle Root of the dataset used for training.
        string datasetMerkleRoot;
        // SHA-256 hash of the trained model file.
        string modelHash;
        // SHA-256 hash of the training configuration file.
        string configHash;
        // Wallet address that registered this model record.
        address registeredBy;
        // Blockchain timestamp when the model was registered.
        uint256 timestamp;
    }

    // Maps a string record ID to its stored ModelRecord.
    mapping(string => ModelRecord) private records;

    // Event emitted whenever a model record is registered.
    event ModelRegistered(
        // Unique model record ID; indexed so blockchain logs can be searched efficiently.
        string indexed recordId,
        // Model name included in the event log.
        string modelName,
        // Model version included in the event log.
        string version,
        // Dataset Merkle Root included in the event log.
        string datasetMerkleRoot,
        // Model file hash included in the event log.
        string modelHash,
        // Config file hash included in the event log.
        string configHash,
        // Address that submitted the registration transaction.
        address registeredBy,
        // Timestamp of the registration transaction.
        uint256 timestamp
    );

    // Stores or updates a model record on-chain.
    function registerModel(
        // Unique ID used to retrieve this record later.
        string memory recordId,
        // Human-readable model name.
        string memory modelName,
        // Model version.
        string memory version,
        // Dataset Merkle Root generated from the training dataset.
        string memory datasetMerkleRoot,
        // Hash of the trained model artifact.
        string memory modelHash,
        // Hash of the model configuration artifact.
        string memory configHash
    ) public {
        // Saves the model record in the records mapping under recordId.
        records[recordId] = ModelRecord(
            // Stores the model name.
            modelName,
            // Stores the model version.
            version,
            // Stores the dataset Merkle Root.
            datasetMerkleRoot,
            // Stores the model hash.
            modelHash,
            // Stores the config hash.
            configHash,
            // Stores the wallet address that called this function.
            msg.sender,
            // Stores the current block timestamp.
            block.timestamp
        );

        // Emits an event so external tools can track the registration in blockchain logs.
        emit ModelRegistered(
            // Event record ID.
            recordId,
            // Event model name.
            modelName,
            // Event model version.
            version,
            // Event dataset Merkle Root.
            datasetMerkleRoot,
            // Event model hash.
            modelHash,
            // Event config hash.
            configHash,
            // Event registering wallet.
            msg.sender,
            // Event timestamp.
            block.timestamp
        );
    }

    // Reads one model record from the blockchain by record ID.
    function getModel(string memory recordId)
    // Makes this function callable by anyone.
    public
    // Marks this as a read-only function that does not change blockchain state.
    view
    // Defines the returned fields.
    returns (
        // Returned model name.
        string memory modelName,
        // Returned version.
        string memory version,
        // Returned dataset Merkle Root.
        string memory datasetMerkleRoot,
        // Returned model hash.
        string memory modelHash,
        // Returned config hash.
        string memory configHash,
        // Returned registering wallet address.
        address registeredBy,
        // Returned timestamp.
        uint256 timestamp
    )
    {
        // Loads the record from storage into memory.
        ModelRecord memory record = records[recordId];

        // Returns all fields of the selected model record.
        return (
            // Returns the model name.
            record.modelName,
            // Returns the version.
            record.version,
            // Returns the dataset Merkle Root.
            record.datasetMerkleRoot,
            // Returns the model hash.
            record.modelHash,
            // Returns the config hash.
            record.configHash,
            // Returns the registering wallet.
            record.registeredBy,
            // Returns the registration timestamp.
            record.timestamp
        );
    }
}
