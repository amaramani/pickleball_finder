import os
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScrapedCourtData:
    """Data class for storing scraped pickleball court information."""
    
    name: Optional[str] = None
    address: Optional[str] = None
    addresslink: Optional[str] = None
    telephone: Optional[str] = None
    websitetext: Optional[str] = None
    websitelink: Optional[str] = None
    courtimage_url: Optional[str] = None
    courtimage_path: Optional[str] = None
    courtimage_type: Optional[str] = None
    image_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def save_image(self, image_data: dict, images_dir: str = "images") -> bool:
        """Save image to file system and update image fields."""
        if not image_data or 'image_data' not in image_data:
            return False
        
        try:
            # Create images directory if it doesn't exist
            os.makedirs(images_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = self._get_file_extension(image_data.get('content_type', 'image/jpeg'))
            filename = f"court_{uuid.uuid4().hex[:8]}{file_extension}"
            filepath = os.path.join(images_dir, filename)
            
            # Decode base64 and save image
            import base64
            image_bytes = base64.b64decode(image_data['image_data'])
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            # Update object fields
            self.courtimage_url = image_data.get('src')
            self.courtimage_path = filepath
            self.courtimage_type = image_data.get('content_type')
            
            return True
            
        except Exception as e:
            print(f"Error saving image: {e}")
            return False
    
    def _get_file_extension(self, content_type: str) -> str:
        """Get file extension from content type."""
        extensions = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        return extensions.get(content_type.lower(), '.jpg')
    
    @classmethod
    def from_scraped_data(cls, h1_heading: str, anchor_links: list, image_data: dict = None):
        """Create ScrapedCourtData object from scraped data."""
        court_data = cls()
        
        # Assign name from h1 heading
        court_data.name = h1_heading
        
        # Assign anchor data (ensure we have at least 3 anchors with defaults)
        anchors = anchor_links + [{'text': '', 'href': ''}] * 3  # Pad with empty anchors
        
        court_data.address = anchors[0]['text'] if len(anchors) > 0 else None
        court_data.addresslink = anchors[0]['href'] if len(anchors) > 0 else None
        court_data.telephone = anchors[1]['text'] if len(anchors) > 1 else None
        court_data.websitetext = anchors[2]['text'] if len(anchors) > 2 else None
        court_data.websitelink = anchors[2]['href'] if len(anchors) > 2 else None
        
        # Store raw image data
        court_data.image_data = image_data
        
        # Save image if provided
        if image_data:
            court_data.save_image(image_data)
        
        return court_data
    
    def to_dict(self, include_image_data: bool = False) -> dict:
        """Convert to dictionary for database storage."""
        result = {
            'name': self.name,
            'address': self.address,
            'addresslink': self.addresslink,
            'telephone': self.telephone,
            'websitetext': self.websitetext,
            'websitelink': self.websitelink,
            'courtimage_url': self.courtimage_url,
            'courtimage_path': self.courtimage_path,
            'courtimage_type': self.courtimage_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_image_data:
            result['image_data'] = self.image_data
        return result
    
    def __repr__(self) -> str:
        """String representation without image data."""
        return f"ScrapedCourtData(name='{self.name}', address='{self.address}', telephone='{self.telephone}', websitetext='{self.websitetext}', image_path='{self.courtimage_path}')"
    
    def __str__(self) -> str:
        return f"ScrapedCourtData(name='{self.name}', address='{self.address}', image_path='{self.courtimage_path}')"