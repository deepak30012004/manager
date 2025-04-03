import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import './visitor.css';

function Visitors() {
  const [role, setRole] = useState(localStorage.getItem("role"));
  const [visitors, setVisitors] = useState([]);
  const [imageDataUrl, setImageDataUrl] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!role) {
      navigate("/login");
    }
    fetchVisitors();
  }, [role]);

  const fetchVisitors = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5000/visitors", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setVisitors(response.data);
    } catch (error) {
      console.error("Error fetching visitors", error);
    }
  };

  const capturePhoto = () => {
    const video = document.createElement("video");
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");

    navigator.mediaDevices.getUserMedia({ video: true })
      .then((stream) => {
        video.srcObject = stream;
        video.play();

        setTimeout(() => {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, canvas.width, canvas.height);

          const dataUrl = canvas.toDataURL("image/jpeg");
          setImageDataUrl(dataUrl);

          stream.getTracks().forEach(track => track.stop());
        }, 1000);
      })
      .catch((error) => console.error("Error accessing webcam: ", error));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!imageDataUrl) {
        alert("Please capture a photo before submitting.");
        return;
    }

    if (role === "staff") {
        const formData = {
            full_name: e.target.full_name.value,
            contact_info: e.target.contact_info.value,
            purpose_of_visit: e.target.purpose_of_visit.value,
            host_employee_name: e.target.host_employee_name.value,
            host_department: e.target.host_department.value,
            company_name: e.target.company_name.value,
            check_in_time: new Date().toISOString(),
            photo: imageDataUrl,
        };

        const token = localStorage.getItem("token");
        try {
            const response = await axios.post("http://localhost:5000/visitors", formData, {
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            });

            alert(response.data.message);
            fetchVisitors();
        } catch (error) {
            console.error("Error adding visitor", error);
        }
    } else {
        alert("Managers cannot add visitors");
    }
  };

  const approveVisitor = async (visitorId) => {
    if (role !== "manager") {
      alert("Only managers can approve visitors");
      return;
    }

    const token = localStorage.getItem("token");
    try {
      const response = await axios.put(
        `http://localhost:5000/visitors/approve/${visitorId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert(response.data.message);
      fetchVisitors();
    } catch (error) {
      console.error("Error approving visitor", error);
    }
  };

  const checkoutVisitor = async (visitorId) => {
    const token = localStorage.getItem("token");
    try {
      const response = await axios.put(
        `http://localhost:5000/visitors/checkout/${visitorId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      alert(response.data.message);
      fetchVisitors(); // Refresh the list of visitors after checkout
    } catch (error) {
      console.error("Error checking out visitor", error);
      alert("Error checking out visitor. Please try again.");
    }
  };
  

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Visitor Management Dashboard</h1>
        <div className="user-role">Role: {role}</div>
        <button onClick={() => navigate("/login")}>Logout</button>
      </header>

      <div className="dashboard-content">
        {/* Staff form for adding visitors */}
        {role === "staff" && (
          <div className="form-container">
            <h2>Add New Visitor</h2>
            <form onSubmit={handleSubmit}>
              <input type="text" name="full_name" placeholder="Full Name" required />
              <input type="text" name="contact_info" placeholder="Contact Info" required />
              <input type="text" name="purpose_of_visit" placeholder="Purpose of Visit" required />
              <input type="text" name="host_employee_name" placeholder="Host Employee Name" required />
              <input type="text" name="host_department" placeholder="Host Department" required />
              <input type="text" name="company_name" placeholder="Company Name" />

              <button type="button" className="capture-btn" onClick={capturePhoto}>
                Capture Photo
              </button>

              {/* Display captured photo */}
              {imageDataUrl && (
                <div className="captured-photo">
                  <h3>Captured Photo</h3>
                  <img src={imageDataUrl} alt="Captured" width="200" />
                </div>
              )}

              <button type="submit">Add Visitor</button>
            </form>
          </div>
        )}

        {/* Table for displaying visitors */}
        <div className="visitor-table-container">
          <h2>Visitors List</h2>
          <table className="visitor-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Contact Info</th>
                <th>Purpose</th>
                <th>Host</th>
                <th>Check-In</th>
                <th>Check-Out</th> {/* New Checkout column */}
                <th>Status</th>
                {role === "manager" && <th>Action</th>}
              </tr>
            </thead>
            <tbody>
  {visitors.map((visitor) => (
    <tr key={visitor.id}>
      <td>{visitor.full_name}</td>
      <td>{visitor.contact_info}</td>
      <td>{visitor.purpose_of_visit}</td>
      <td>{visitor.host_employee_name}</td>
      <td>{visitor.check_in_time || "N/A"}</td>
      <td>{visitor.check_out_time || "N/A"}</td> {/* Display checkout time */}
      <td>{visitor.status}</td>
      {role === "manager" && (
        <td>
          {visitor.status === 'pending' && (
            <button className="approve-btn" onClick={() => approveVisitor(visitor.id)}>
              Approve
            </button>
          )}
          {visitor.status === 'approved' && !visitor.check_out_time && (
            <button className="checkout-btn" onClick={() => checkoutVisitor(visitor.id)}>
              Checkout
            </button>
          )}
        </td>
      )}
      {role === "staff" && visitor.status === 'approved' && !visitor.check_out_time && (
        <td>
          <button className="checkout-btn" onClick={() => checkoutVisitor(visitor.id)}>
            Checkout
          </button>
        </td>
      )}
    </tr>
  ))}
</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Visitors;
