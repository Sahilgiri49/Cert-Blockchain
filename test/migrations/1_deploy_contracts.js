const CertificateRegistry = artifacts.require("CertificateRegistry");

module.exports = async function(deployer, network, accounts) {
  await deployer.deploy(CertificateRegistry);
  
  // If we're on development network, set up initial state
  if (network === 'development' || network === 'ganache') {
    const instance = await CertificateRegistry.deployed();
    
    // Add the first university (using the second account as university)
    await instance.addUniversity(accounts[1], { from: accounts[0] });
  }
}; 