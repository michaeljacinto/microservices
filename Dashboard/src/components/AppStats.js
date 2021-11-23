import React, { useEffect, useState } from "react";
import "../App.css";

export default function AppStats() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [stats, setStats] = useState({});
  const [error, setError] = useState(null);

  const getStats = () => {
    fetch(`http://michaeljacinto.westus2.cloudapp.azure.com/processing/stats`)
      .then((res) => res.json())
      .then(
        (result) => {
          console.log("Received Stats");
          setStats(result);
          setIsLoaded(true);
        },
        (error) => {
          setError(error);
          setIsLoaded(true);
        }
      );
  };
  useEffect(() => {
    const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, [getStats]);

  if (error) {
    return <div className={"error"}>Error found when fetching from API</div>;
  } else if (isLoaded === false) {
    return <div>Loading...</div>;
  } else if (isLoaded === true) {
    return (
      <div>
        <h1>Latest Stats</h1>
        <table className={"StatsTable"}>
          <tbody>
            <tr>
              <th>Sell Orders</th>
              <th>Buy Orders</th>
            </tr>
            <tr>
              <td># Stock Sell Orders: {stats["num_stock_sell_orders"]}</td>
              <td># Stock Buy Orders: {stats["num_stock_buy_orders"]}</td>
            </tr>
            <tr>
              <td colspan="2">
                Max Stock Sell Quantity: {stats["max_stock_sell_qty"]}
              </td>
            </tr>
            <tr>
              <td colspan="2">
                Max Stock Buy Quantity: {stats["max_stock_buy_qty"]}
              </td>
            </tr>
            <tr>
              <td colspan="2">
                Minimum Stock Ask Price: {stats["min_stock_ask_price"]}
              </td>
            </tr>
            <tr>
              <td colspan="2">
                Minimum Stock Bid Price: {stats["min_stock_bid_price"]}
              </td>
            </tr>
          </tbody>
        </table>
        <h3>Last Updated: {stats["last_updated"]}</h3>
      </div>
    );
  }
}
